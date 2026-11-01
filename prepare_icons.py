"""Prepare the official marks for the README.

Three fixes applied here:

1. Wordmarks replaced with symbol-only variants where the collection offers them, so the
   row is a set of comparable marks rather than a mix of logos and logotypes.
2. Iconify returns width/height in `em` units, which resolve against the surrounding font
   size. Each SVG is rewritten with pixel dimensions taken from its own viewBox aspect
   ratio, so marks keep their real proportions instead of being squashed into squares.
3. Linux (black Tux) and X (no fill, inherits text colour) are invisible on the dark theme,
   so a light copy of each is generated and served through <picture>.
"""
import pathlib
import re
import urllib.request

API = "https://api.iconify.design"
SRC = pathlib.Path("official")
DST = pathlib.Path("docs/icons")
BASE_HEIGHT = 48

# key -> Iconify name. Symbol variants where available.
ICONS = {
    "kotlin": "logos:kotlin-icon",
    "java": "logos:java",
    "cpp": "logos:c-plusplus",
    "python": "logos:python",
    "fastapi": "logos:fastapi-icon",
    "nodejs": "logos:nodejs",
    "react": "logos:react",
    "javascript": "logos:javascript",
    "tailwindcss": "logos:tailwindcss-icon",
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


def normalize(svg_text):
    """Give the root <svg> pixel dimensions that match its viewBox aspect ratio."""
    vb = re.search(r'viewBox="([-\d.]+)\s+([-\d.]+)\s+([\d.]+)\s+([\d.]+)"', svg_text)
    if not vb:
        return svg_text, None
    vw, vh = float(vb.group(3)), float(vb.group(4))
    w = round(BASE_HEIGHT * vw / vh)
    out = re.sub(r'\swidth="[^"]*"', f' width="{w}"', svg_text, count=1)
    out = re.sub(r'\sheight="[^"]*"', f' height="{BASE_HEIGHT}"', out, count=1)
    return out, (w, BASE_HEIGHT)


DST.mkdir(parents=True, exist_ok=True)
report = []
for key, name in ICONS.items():
    raw = get(f"{API}/{name.replace(':', '/', 1)}.svg").decode("utf-8")
    SRC.joinpath(f"{key}.svg").write_text(raw, encoding="utf-8")
    fixed, dims = normalize(raw)
    DST.joinpath(f"{key}.svg").write_text(fixed, encoding="utf-8")
    report.append((key, dims))

# Light-theme copies for the two marks that disappear on a dark background.
tux = DST.joinpath("linux.svg").read_text(encoding="utf-8")
DST.joinpath("linux-dark.svg").write_text(
    tux.replace('fill="#000"', 'fill="#e6edf3"').replace('stroke="#000"', 'stroke="#e6edf3"'),
    encoding="utf-8")

xsvg = DST.joinpath("x.svg").read_text(encoding="utf-8")
# Give the light-theme copy an explicit black fill; the dark copy gets a near-white one.
DST.joinpath("x.svg").write_text(xsvg.replace("<path ", '<path fill="#000000" ', 1),
                                 encoding="utf-8")
DST.joinpath("x-dark.svg").write_text(xsvg.replace("<path ", '<path fill="#f0f3f6" ', 1),
                                      encoding="utf-8")

for key, dims in report:
    print(f"  {key:12} {dims}")
print(f"\nwrote {len(list(DST.glob('*.svg')))} files to docs/icons")
