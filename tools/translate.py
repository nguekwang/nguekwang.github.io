#!/usr/bin/env python3
"""Translate changed English page text into every machine-translated language with Claude.

The source is data/i18n/en.yaml. A "unit" is one text value, or one whole list (such as
`projects`), at a path in en.yaml. Settings: data/translation.yaml.

  python3 tools/translate.py --base REF
      Translate every unit whose English differs from en.yaml at git REF, and every unit that is
      missing from a language, into each machine-translated language (mt_notice is not empty).
      Units that did not change are left exactly as they are. Writes data/i18n/<code>.yaml.
      Uses the Claude Agent SDK; in CI it signs in with CLAUDE_CODE_OAUTH_TOKEN.
  python3 tools/translate.py --base REF --dry-run
      Only list what would be translated.
  python3 tools/translate.py --check
      Fail when a machine-translated language drops a protected term or {placeholder} that its
      English text contains (run on every pull request).
  python3 tools/translate.py --base REF --stale
      Warn (never fail) about languages whose text did not change although the English did,
      including the owner-written languages, which are updated by hand.
"""
import argparse, asyncio, io, json, os, re, subprocess, sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import DATA, REFERENCE, ROOT, compare  # noqa: E402

PLACEHOLDER = re.compile(r"\{\w+\}")
# Spaces that look like an ordinary space in an editor; the language files write them as \uXXXX
# inside double-quoted strings (for example French "\u00a0: "), and so does write_language().
# Joiners such as U+200C are left as they are: they are part of the spelling (Persian, Hindi).
INVISIBLE_SPACES = {"\u00a0", "\u202f", "\u2009"}
# Languages translated at the same time (one Claude request each).
PARALLEL = 4
# A response that fails validation is asked for once more, with the problems listed.
ATTEMPTS = 2


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def settings():
    site = load_yaml(os.path.join(DATA, "site.yaml"))
    cfg = load_yaml(os.path.join(DATA, "translation.yaml"))
    texts = {c: load_yaml(os.path.join(DATA, "i18n", c + ".yaml")) for c in site["languages"]}
    return site, cfg, texts


def machine_translated(site, texts):
    """Languages that show a machine-translation notice; the others are written by the owner."""
    return [c for c in site["languages"] if c != REFERENCE and texts[c].get("mt_notice")]


def units(data, own_keys, path=()):
    """Paths of the translatable units: every text value, and every list as one unit."""
    if isinstance(data, dict):
        for k, v in data.items():
            if path or k not in own_keys:
                yield from units(v, own_keys, path + (k,))
    else:
        yield path


def get(data, path):
    for k in path:
        if isinstance(data, dict) and k in data:
            data = data[k]
        else:
            return None
    return data


def same_shape(path, ref, value):
    errors = []
    compare(ref, value, key(path), errors)
    return not errors


def protected(cfg, en):
    terms = list(cfg.get("protected_terms") or [])
    terms += [p["name"] for p in en.get("projects") or [] if p.get("name")]
    return terms


def strings(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from strings(v)
    elif isinstance(value, str):
        yield value


def missing_terms(terms, en_value, value):
    """Protected terms and placeholders in the English unit that its translation lacks."""
    en_text = "\n".join(strings(en_value))
    text = "\n".join(strings(value))
    wanted = [t for t in terms if t in en_text] + sorted(set(PLACEHOLDER.findall(en_text)))
    return [t for t in wanted if text.count(t) < en_text.count(t)]


def file_at(ref, code):
    """data/i18n/<code>.yaml as it was at git ref ({} if it did not exist)."""
    rel = os.path.relpath(os.path.join(DATA, "i18n", code + ".yaml"), ROOT)
    out = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=ROOT, capture_output=True, text=True)
    return (yaml.safe_load(out.stdout) or {}) if out.returncode == 0 else {}


def changed_units(en, base_en, own_keys):
    return [p for p in units(en, own_keys) if get(base_en, p) != get(en, p)]


def todo(en, base_en, texts, codes, own_keys):
    """For each language, the units to translate: changed in English, or missing or misshapen."""
    changed = set(changed_units(en, base_en, own_keys))
    jobs = {}
    for code in codes:
        paths = [p for p in units(en, own_keys)
                 if p in changed or get(texts[code], p) is None or not same_shape(p, get(en, p), get(texts[code], p))]
        if paths:
            jobs[code] = paths
    return jobs


def schema_of(value):
    """JSON schema with the same shape as an English unit, so Claude answers in that shape."""
    if isinstance(value, dict):
        return {"type": "object", "additionalProperties": False, "required": list(value),
                "properties": {k: schema_of(v) for k, v in value.items()}}
    if isinstance(value, list):
        return {"type": "array", "minItems": len(value), "maxItems": len(value),
                "items": schema_of(value[0]) if value else {"type": "string"}}
    return {"type": "string"}


def key(path):
    """A unit's path as build.py --check writes it, such as keywords.typology."""
    return ".".join(str(p) for p in path)


def language_name(code):
    from babel import Locale
    return Locale.parse(code, sep="-").english_name


SYSTEM = """You translate the text of a linguist's personal research website from English into {name} ({code}).
Rules:
- Write as this language's modern official documents and academic websites write: register, punctuation, brackets, spacing, quotation marks and digits. Where the current page already uses a convention (see the current file), keep it.
- Keep these exactly as written in English, wherever they appear: {terms}.
- Keep every placeholder in braces, such as {{date}}, exactly once and unchanged.
- Keep the meaning; add nothing, drop nothing, no explanations.
- A value that is a list must stay a list of the same length; in a list of objects, keep every key and translate only the text values.
Return only a JSON object with exactly the keys you were given, each mapped to its translation."""

PROMPT = """Current {code}.yaml of the site (for context and existing conventions; do not translate it):
```yaml
{current}
```

Translate each of these English values. Each key is the value's path in the file; "previous" is the
current {name} text for that path, if any (keep its wording where the English meaning did not change).
```json
{units}
```"""


async def ask(cfg, system, prompt, schema):
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query
    options = ClaudeAgentOptions(
        model=cfg["model"], effort=cfg.get("effort"), system_prompt=system,
        tools=[], allowed_tools=[], setting_sources=[], max_turns=3,
        output_format={"type": "json_schema", "schema": schema},
    )
    result = None
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            result = message
    if result is None or result.is_error:
        raise RuntimeError(f"Claude returned no result: {getattr(result, 'errors', None)}")
    if result.structured_output is not None:
        return result.structured_output
    text = (result.result or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    return json.loads(text)


def validate(en, paths, terms, answer):
    problems = []
    for p in paths:
        k = key(p)
        if k not in answer:
            problems.append(f"{k}: missing")
            continue
        errors = []
        compare(get(en, p), answer[k], k, errors)
        problems += errors
        lost = missing_terms(terms, get(en, p), answer[k])
        if lost:
            problems.append(f"{k}: must keep {', '.join(lost)} as written")
    return problems


async def translate(cfg, en, texts, code, paths, terms, limit):
    name = language_name(code)
    with open(os.path.join(DATA, "i18n", code + ".yaml"), encoding="utf-8") as f:
        current = f.read()
    payload = {key(p): {"english": get(en, p), "previous": get(texts[code], p)} for p in paths}
    schema = {"type": "object", "additionalProperties": False, "required": list(payload),
              "properties": {key(p): schema_of(get(en, p)) for p in paths}}
    system = SYSTEM.format(name=name, code=code, terms=", ".join(terms))
    prompt = PROMPT.format(code=code, name=name, current=current,
                           units=json.dumps(payload, ensure_ascii=False, indent=1))
    async with limit:
        for attempt in range(ATTEMPTS):
            answer = await ask(cfg, system, prompt, schema)
            problems = validate(en, paths, terms, answer)
            if not problems:
                print(f"{code}: translated {len(paths)} unit(s)")
                return code, {p: answer[key(p)] for p in paths}
            print(f"{code}: attempt {attempt + 1} rejected: {'; '.join(problems)}", file=sys.stderr)
            prompt += "\n\nYour previous answer had these problems; fix them:\n" + "\n".join(problems)
    raise SystemExit(f"{code}: no valid translation after {ATTEMPTS} attempts")


def round_trip():
    from ruamel.yaml import YAML
    y = YAML()
    y.preserve_quotes = True
    y.width = 10 ** 6  # never wrap long lines
    y.indent(mapping=2, sequence=2, offset=0)
    return y


def escape_invisible(text):
    """Write invisible characters inside double-quoted strings as \\uXXXX, as the files do by hand."""
    def fix(m):
        return "".join(f"\\u{ord(ch):04x}" if ch in INVISIBLE_SPACES else ch for ch in m.group(0))
    return re.sub(r'"(?:[^"\\\n]|\\.)*"', fix, text)


def write_language(code, en, own_keys, results):
    """Put the new translations into data/i18n/<code>.yaml, keeping every other line as it is."""
    path = os.path.join(DATA, "i18n", code + ".yaml")
    y = round_trip()
    with open(path, encoding="utf-8") as f:
        doc = y.load(f)
    for p, value in results.items():
        node = doc
        for depth, k in enumerate(p[:-1]):
            if k not in node:
                node.insert(list(get(en, p[:depth]).keys()).index(k), k, {})
            node = node[k]
        last = p[-1]
        if last in node:
            node[last] = value
        else:
            node.insert(min(list(get(en, p[:-1]).keys()).index(last), len(node)), last, value)
    prune(doc, en, own_keys, top=True)
    out = io.StringIO()
    y.dump(doc, out)
    text = escape_invisible(out.getvalue())  # finish before opening the file, so an error never empties it
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def prune(node, en, own_keys, top=False):
    """Remove keys that English no longer has (except each language's own keys)."""
    if not isinstance(node, dict) or not isinstance(en, dict):
        return
    for k in list(node.keys()):
        if top and k in own_keys:
            continue
        if k not in en:
            del node[k]
        else:
            prune(node[k], en[k], own_keys)


def check_terms(cfg, en, texts, codes):
    terms = protected(cfg, en)
    own = set(cfg.get("own_keys") or [])
    errors = []
    for code in codes:
        for p in units(en, own):
            lost = missing_terms(terms, get(en, p), get(texts[code], p))
            if lost:
                errors.append(f"data/i18n/{code}.yaml {key(p)}: must keep {', '.join(lost)} as written in English")
    return errors


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", help="git ref whose English text counts as already translated")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--stale", action="store_true")
    args = ap.parse_args()
    site, cfg, texts = settings()
    en = texts[REFERENCE]
    own = set(cfg.get("own_keys") or [])
    codes = machine_translated(site, texts)

    if args.check:
        errors = check_terms(cfg, en, texts, codes)
        if errors:
            print(f"{len(errors)} translation(s) lost a protected term:", file=sys.stderr)
            for e in errors:
                print("  " + e, file=sys.stderr)
            sys.exit(1)
        print(f"translations OK: {len(codes)} machine-translated languages keep every protected term")
        return

    if not args.base:
        ap.error("--base is required")
    base_en = file_at(args.base, REFERENCE)

    if args.stale:
        others = [c for c in site["languages"] if c != REFERENCE]
        base = {c: file_at(args.base, c) for c in others}
        for p in changed_units(en, base_en, own):
            same = [c for c in others if get(base[c], p) == get(texts[c], p)]
            if same:
                owner = [c for c in same if c not in codes]
                print(f"::warning file=data/i18n/{REFERENCE}.yaml::English '{key(p)}' changed but not in: "
                      f"{', '.join(same)}" + (f" (written by the owner: {', '.join(owner)})" if owner else ""))
        return

    jobs = todo(en, base_en, texts, codes, own)
    if not jobs:
        print("nothing to translate")
        return
    for code, paths in jobs.items():
        print(f"{code}: {', '.join(key(p) for p in paths)}")
    if args.dry_run:
        return
    terms = protected(cfg, en)

    async def run():
        limit = asyncio.Semaphore(PARALLEL)
        return await asyncio.gather(*(translate(cfg, en, texts, c, ps, terms, limit) for c, ps in jobs.items()))

    for code, results in asyncio.run(run()):
        write_language(code, en, own, results)


if __name__ == "__main__":
    main()
