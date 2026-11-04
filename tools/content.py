"""data/ の TOML を読み、build.py が使う形にして返す。文言はすべて data/ にあり、ここには書かない。"""
import os, tomllib

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def _load(*p):
    with open(os.path.join(DATA, *p), "rb") as f:
        return tomllib.load(f)

SITE_CONF = _load("site.toml")
LANGS = []
for code in SITE_CONF["languages"]:
    d = _load("i18n", code + ".toml")
    d["code"] = code
    d["mt"] = d.get("mt_notice") or None
    d["projects"] = [[p["name"], p["desc"]] for p in d.get("projects", [])]
    LANGS.append(d)
NEW = {L["code"]: L for L in LANGS}          # 互換のため(build.py は N[...] でも参照する)
UNPUB = {L["code"]: L["unpublished"] for L in LANGS}
_kw = _load("keywords.toml").get("keyword", [])
KEYWORDS = {L["code"]: (L["keywords_h"], [k.get(L["code"]) or k["en"] for k in _kw]) for L in LANGS}
TALKS = _load("talks.toml").get("talk", [])
