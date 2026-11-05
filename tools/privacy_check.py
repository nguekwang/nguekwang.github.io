#!/usr/bin/env python3
"""Fail when the repository contains personal information the owner has not approved.

Scans every file tracked by git (text files only) for:
  - email addresses not listed in data/privacy.yaml
  - phone numbers (Japanese and international formats)
  - Japanese postal codes and street addresses (〒, 123-4567, 丁目, 番地, 1-2-3)
  - full birth dates: a date with a day on a line that mentions birth (in any site language),
    and any year-month-day date written in the CJK style (2003年12月5日) in page text

Anything found is printed as file:line and the script exits with status 1, unless the exact
match is listed under `strings` (or the address under `emails` / `email_domains`) in
data/privacy.yaml. Add an entry there only after the owner has approved publishing it.

This is a safety net, not a proof: it cannot recognise every way of writing an address or a
date, so the manual check before committing (CLAUDE.md) still applies.

Usage: python3 tools/privacy_check.py
"""
import os, re, subprocess, sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOW_FILE = "data/privacy.yaml"
# This script holds example numbers in its own comments and patterns.
SKIP = {"tools/privacy_check.py"}

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})")
PHONE = [
    # Japanese numbers: 03-1234-5678, 090-1234-5678, 0120 123 456, 09012345678
    re.compile(r"(?<![\d-])0\d{1,4}[-‐ ]\d{1,4}[-‐ ]\d{3,4}(?![\d-])"),
    re.compile(r"(?<!\d)0[5789]0\d{8}(?!\d)"),
    # International numbers: +81 90-1234-5678, +1 (555) 123-4567
    re.compile(r"\+\d{1,3}[\s-]?\(?\d{1,4}\)?[\s-]?\d{2,4}[\s-]?\d{3,4}(?!\d)"),
]
ADDRESS = [
    re.compile(r"〒\s*\d{3}-?\d{4}"),
    re.compile(r"(?<![\d-])\d{3}-\d{4}(?![\d-])"),          # postal code
    re.compile(r"\d+\s*(?:丁目|番地|番\s*\d+\s*号)"),
    re.compile(r"(?<![\d-])\d{1,2}-\d{1,2}-\d{1,3}(?![\d-])"),  # chome-ban-go, e.g. 1-2-3
]
# Words that mean "born" / "birth" in the site's languages.
BIRTH_WORDS = re.compile(
    r"born|birth|生まれ|生年月日|誕生|出生|出生于|태어|생년월일|nacid[oa]|nacimiento|n[ée]e?\b|naissance|"
    r"родил|рожд|народ|geboren|geburt|nat[oa]\b|nascit|nascid|geboren|doğ|lahir|เกิด|जन्म|"
    r"تولد|ولد|ميلاد|urodz|sinh",
    re.IGNORECASE,
)
FULL_DATE = [
    re.compile(r"\d{4}\s*[-/.年년]\s*\d{1,2}\s*[-/.月월]\s*\d{1,2}(?!\d)"),  # 2003-12-05, 2003年12月5日
    re.compile(r"(?<!\d)\d{1,2}\s*[./-]\s*\d{1,2}\s*[./-]\s*\d{4}"),       # 05.12.2003, 12/5/2003
    re.compile(r"(?<!\d)\d{1,2}(?:st|nd|rd|th|er|\.)?\s+(?:de\s+)?(?!năm\b)[^\W\d_]{3,}\.?\s+(?:de\s+)?\d{4}"),  # 5 December 2003 (not vi "tháng 12 năm 2003")
    re.compile(r"[^\W\d_]{3,}\.?\s+\d{1,2},\s*\d{4}"),                     # December 5, 2003
]
CJK_FULL_DATE = re.compile(r"\d{4}\s*[年년]\s*\d{1,2}\s*[月월]\s*\d{1,2}\s*[日일]")


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [p for p in out.decode().split("\0") if p]


def read_text(path):
    try:
        with open(os.path.join(ROOT, path), encoding="utf-8") as f:
            return f.read()
    except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
        return None


def scan(path, text, allow):
    found = []
    page_text = path.startswith("data/i18n/")
    for n, line in enumerate(text.splitlines(), 1):
        hits = []
        for m in EMAIL.finditer(line):
            addr, domain = m.group(0), m.group(1).lower()
            if addr.lower() not in allow["emails"] and domain not in allow["email_domains"]:
                hits.append(("email address", addr))
        for kind, patterns in (("phone number", PHONE), ("postal code or address", ADDRESS)):
            for p in patterns:
                hits += [(kind, m.group(0)) for m in p.finditer(line)]
        if BIRTH_WORDS.search(line):
            for p in FULL_DATE:
                hits += [("full date on a line about birth", m.group(0)) for m in p.finditer(line)]
        if page_text:
            hits += [("full date in page text", m.group(0)) for m in CJK_FULL_DATE.finditer(line)]
        for kind, match in hits:
            if match.strip() not in allow["strings"]:
                found.append(f"{path}:{n}: {kind}: {match.strip()}")
    return found


def main():
    with open(os.path.join(ROOT, ALLOW_FILE), encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    allow = {
        "emails": {e.lower() for e in cfg.get("emails") or []},
        "email_domains": {d.lower() for d in cfg.get("email_domains") or []},
        "strings": set(cfg.get("strings") or []),
    }
    problems = []
    for path in tracked_files():
        if path in SKIP:
            continue
        text = read_text(path)
        if text is not None:
            problems += scan(path, text, allow)
    # De-duplicate (several patterns can match the same text).
    problems = list(dict.fromkeys(problems))
    if problems:
        print(f"{len(problems)} possible piece(s) of personal information:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        print(f"If the owner approved publishing one of these, add it to {ALLOW_FILE}.", file=sys.stderr)
        sys.exit(1)
    print("privacy check OK: no unapproved personal information found")


if __name__ == "__main__":
    main()
