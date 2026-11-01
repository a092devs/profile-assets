"""Fetch official full-colour brand marks from the Iconify `logos` collection
(Gil Barbara's SVG Logos, CC0). Names are pinned explicitly so a fuzzy ranking
can't silently substitute a different project's logo.

The SVGs are committed to the assets repo, so the profile has no runtime
dependency on Iconify.
"""
import json
import pathlib
import urllib.request

API = "https://api.iconify.design"

# key -> exact Iconify icon name
ICONS = {
    "kotlin": "logos:kotlin",
    "java": "logos:java",
    "cpp": "logos:c-plusplus",
    "python": "logos:python",
    "fastapi": "logos:fastapi",
    "nodejs": "logos:nodejs",
    "react": "logos:react",
    "javascript": "logos:javascript",
    "tailwindcss": "logos:tailwindcss",
    "postgresql": "logos:postgresql",
    "docker": "logos:docker-icon",
    "git": "logos:git-icon",
    "linux": "logos:linux-tux",
    "linkedin": "logos:linkedin-icon",
    "x": "logos:x",
    "gmail": "logos:google-gmail",
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-assets-build"})
    return urllib.request.urlopen(req, timeout=30).read()


out = pathlib.Path("official")
out.mkdir(exist_ok=True)
ok, missing = [], []
for key, name in ICONS.items():
    url = f"{API}/{name.replace(':', '/', 1)}.svg"
    try:
        svg = get(url)
    except Exception as exc:
        missing.append((key, name, str(exc)))
        continue
    (out / f"{key}.svg").write_bytes(svg)
    ok.append(key)
    print(f"  {key:12} <- {name}")

print(f"\nok {len(ok)}/{len(ICONS)}")
for m in missing:
    print("  MISSING", m)
json.dump({k: ICONS[k] for k in ok}, open("official/_names.json", "w"), indent=1)
