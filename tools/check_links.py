#!/usr/bin/env python3
"""Check that every link between the site's own pages points at a file that exists.

Reads the built site (_site/ by default) and checks every href and src in every HTML file:
relative links, root-relative links (/style.css) and absolute links under site.url
(canonical, hreflang alternates). Project sites under site.url (`site` in data/ai_tools.yaml,
such as /<repository name>/) are published from their own repositories, so they count as other
sites. Links to other sites are not checked here; the weekly
workflow .github/workflows/links.yml checks those with lychee. Also checks that every
<loc> and alternate in sitemap.xml exists.

Usage: python3 tools/check_links.py [SITE_DIR]
"""
import html.parser, os, re, sys, urllib.parse

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.links.append(value)


def target(site_dir, site_url, page, link, project_sites=()):
    """Return the local path a link points to, or None when it leaves the site."""
    link = link.split("#", 1)[0].split("?", 1)[0]
    if not link:
        return None
    if any(link.startswith(p) for p in project_sites):
        return None  # a project site published from its own repository
    if link.startswith(site_url + "/") or link == site_url:
        rel = link[len(site_url):] or "/"
        return os.path.join(site_dir, urllib.parse.unquote(rel).lstrip("/"))
    if re.match(r"^[a-z][a-z0-9+.-]*:", link, re.IGNORECASE) or link.startswith("//"):
        return None  # another site, mailto:, data:, ...
    if link.startswith("/"):
        return os.path.join(site_dir, urllib.parse.unquote(link).lstrip("/"))
    return os.path.normpath(os.path.join(os.path.dirname(page), urllib.parse.unquote(link)))


def exists(path):
    return os.path.isfile(path) or os.path.isfile(os.path.join(path, "index.html"))


def main():
    site_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "_site"))
    with open(os.path.join(ROOT, "data", "site.yaml"), encoding="utf-8") as f:
        site_url = yaml.safe_load(f)["url"].rstrip("/")
    with open(os.path.join(ROOT, "data", "ai_tools.yaml"), encoding="utf-8") as f:
        projects = (yaml.safe_load(f) or {}).get("projects") or {}
    project_sites = [p["site"] for p in projects.values() if (p or {}).get("site")]
    broken, checked = [], 0
    for dirpath, _, files in os.walk(site_dir):
        for name in files:
            page = os.path.join(dirpath, name)
            if name.endswith(".html"):
                parser = Links()
                with open(page, encoding="utf-8") as f:
                    parser.feed(f.read())
                links = parser.links
            elif name == "sitemap.xml":
                with open(page, encoding="utf-8") as f:
                    links = re.findall(r'(?:<loc>|href=")([^<"]+)', f.read())
            else:
                continue
            for link in links:
                path = target(site_dir, site_url, page, link, project_sites)
                if path is None:
                    continue
                checked += 1
                if not exists(path):
                    broken.append(f"{os.path.relpath(page, site_dir)}: {link}")
    if broken:
        print(f"{len(broken)} broken link(s) inside the site:", file=sys.stderr)
        for b in sorted(set(broken)):
            print("  " + b, file=sys.stderr)
        sys.exit(1)
    print(f"links OK: {checked} links inside the site all point at existing files")


if __name__ == "__main__":
    main()
