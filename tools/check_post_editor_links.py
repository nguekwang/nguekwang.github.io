#!/usr/bin/env python3
"""Check the links of post-editors (data/post_editors.yaml) and email the owner about broken ones.

Run weekly by .github/workflows/post-editor-links.yml. When a link stops working, the owner
gets an email through Gmail so they can contact that person. Nothing is written to an issue, and
the public workflow log shows only counts, never names or URLs.

Environment (repository secrets):
  GMAIL_ADDRESS       the Gmail account that sends the email
  GMAIL_APP_PASSWORD  an app password for that account (Google Account > Security > App passwords)
The email goes to `email` in data/site.yaml.

Exit status: 0 when every link works or the email was sent; 1 when links are broken and no email
could be sent (GitHub then reports the failed run to the owner instead).
"""
import os, smtplib, ssl, sys, time, urllib.error, urllib.request
from email.message import EmailMessage

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# A generic client name; many sites refuse requests without a browser-like User-Agent.
USER_AGENT = "Mozilla/5.0 (compatible; link-check; +https://github.com/nguekwang/nguekwang.github.io)"
# Answers that mean "the page exists but refuses robots" (common on social media). Not broken.
BLOCKED = {401, 403, 429, 999}
RETRY_AFTER = 30  # seconds before the second try, so a short outage is not reported


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def status(url):
    """Return an HTTP status code, or an error description when the server could not be reached."""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in {405, 501} | BLOCKED:
                continue  # some servers do not answer HEAD; try GET
            return e.code
        except (urllib.error.URLError, OSError) as e:
            if method == "HEAD":
                continue
            return f"unreachable ({getattr(e, 'reason', e)})"
    return "unreachable"


def is_broken(result):
    return not isinstance(result, int) or (result >= 400 and result not in BLOCKED)


def send_mail(to, broken):
    sender = os.environ.get("GMAIL_ADDRESS", "").strip()
    password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if not sender or not password:
        print("GMAIL_ADDRESS / GMAIL_APP_PASSWORD are not set, so no email was sent.")
        return False
    lines = [
        f"{len(broken)} post-editor link(s) on https://nguekwang.github.io/ do not work.",
        "Please contact each person and ask for a new link, or remove the link",
        "from data/post_editors.yaml.",
        "",
    ]
    for code, name, url, result in broken:
        lines += [f"- Language: {code}", f"  Name: {name}", f"  Link: {url}", f"  Result: {result}", ""]
    run = os.environ.get("GITHUB_RUN_URL")
    if run:
        lines.append(f"Workflow run: {run}")
    msg = EmailMessage()
    msg["Subject"] = f"[nguekwang.github.io] {len(broken)} post-editor link(s) are broken"
    msg["From"] = sender
    msg["To"] = to
    msg.set_content("\n".join(lines))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as s:
        s.login(sender, password)
        s.send_message(msg)
    return True


def main():
    site = load("site.yaml")
    people = (load("post_editors.yaml").get("post_editors")) or {}
    links = [(code, p["name"], p["url"]) for code, ps in people.items() for p in ps if p.get("url")]
    if not links:
        print("No post-editor links to check.")
        return 0
    broken = [(c, n, u, status(u)) for c, n, u in links]
    broken = [b for b in broken if is_broken(b[3])]
    if broken:
        time.sleep(RETRY_AFTER)
        broken = [(c, n, u, status(u)) for c, n, u, _ in broken]
        broken = [b for b in broken if is_broken(b[3])]
    # The log is public: print counts only.
    print(f"Checked {len(links)} post-editor link(s); {len(broken)} broken.")
    if not broken:
        return 0
    if send_mail(site["email"], broken):
        print("The details were emailed to the owner.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
