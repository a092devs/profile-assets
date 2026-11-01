"""Builds the GitHub profile assets locally: brand icons, an animated typing
banner, and the stats cards. Everything is emitted as PNG or GIF because GitHub
serves repo-hosted SVG as text/plain, which breaks <img>.
"""
import io
import json
import subprocess
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

OUT = Path(__file__).parent / "assets"
(OUT / "icons").mkdir(parents=True, exist_ok=True)

USER = "a092devs"
ICON_SLUGS = [
    "kotlin", "openjdk", "cplusplus", "python", "fastapi", "nodedotjs", "react",
    "javascript", "tailwindcss", "postgresql", "docker", "git", "linux",
]
# Brand marks come from the simple-icons set (CC0); the hex values are the
# published brand colours for each technology.
BRAND_HEX = {
    "kotlin": "7F52FF", "openjdk": "007396", "cplusplus": "00599C",
    "python": "3776AB", "fastapi": "009485", "nodedotjs": "339933",
    "react": "61DAFB", "javascript": "F7DF1E", "tailwindcss": "06B6D4",
    "postgresql": "4169E1", "docker": "2496ED", "git": "F05032",
    "linux": "FCC624",
}
def find_font(*names):
    """Works both on this Windows box and on the ubuntu runner that refreshes nightly."""
    import glob
    roots = ["C:/Windows/Fonts", "/usr/share/fonts/truetype",
             "/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation",
             "/usr/share/fonts"]
    for root in roots:
        for name in names:
            hits = glob.glob(f"{root}/**/{name}", recursive=True)
            if hits:
                return hits[0]
    return None


FONT = find_font("consola.ttf", "DejaVuSansMono.ttf", "LiberationMono-Regular.ttf")
FONT_B = find_font("consolab.ttf", "DejaVuSansMono-Bold.ttf", "LiberationMono-Bold.ttf") or FONT

DARK = {"bg": "#0d1117", "fg": "#58a6ff", "text": "#c9d1d9", "muted": "#8b949e",
        "line": "#30363d", "card": "#161b22"}
LIGHT = {"bg": "#ffffff", "fg": "#0969da", "text": "#1f2328", "muted": "#57606a",
         "line": "#d0d7de", "card": "#f6f8fa"}

PHRASES = [
    "Android Development & Patching",
    "Full-Stack Web & Backend APIs",
    "Data Analytics & ETL Workflows",
]


def api(path):
    raw = subprocess.run(["gh", "api", path, "--jq", "."],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(raw)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-assets-build"})
    return urllib.request.urlopen(req, timeout=30).read()


def repo_languages():
    """GitHub exposes no user-languages endpoint, so sum it across owned repos."""
    totals = {}
    for r in api(f"users/{USER}/repos?per_page=100"):
        if r["fork"]:
            continue
        try:
            for name, size in api(f"repos/{r['full_name']}/languages").items():
                totals[name] = totals.get(name, 0) + size
        except Exception:
            pass
    return sorted([{"name": k, "bytes": v} for k, v in totals.items()],
                  key=lambda l: -l["bytes"])


def build_icons():
    made = []
    for slug in ICON_SLUGS:
        url = f"https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/{slug}.svg"
        try:
            data = fetch(url)
        except Exception as exc:
            print(f"  ! {slug}: fetch failed ({exc})")
            continue
        drawing = svg2rlg(io.BytesIO(data))
        if drawing is None:
            print(f"  ! {slug}: parse failed")
            continue
        longest = max(drawing.width, drawing.height) or 1
        scale = 256.0 / longest
        drawing.scale(scale, scale)
        drawing.width, drawing.height = drawing.width * scale, drawing.height * scale
        png = io.BytesIO()
        renderPM.drawToFile(drawing, png, fmt="PNG")
        png.seek(0)
        raster = Image.open(png).convert("RGBA")
        alpha = raster.getchannel("A")
        if alpha.getextrema()[0] < 250:
            # Renderer honoured transparency: use it directly.
            mask = alpha
        else:
            # Flat opaque canvas: the mark is the dark part of the luminance.
            mask = raster.convert("L").point(lambda v: 255 - v)
        hexc = BRAND_HEX.get(slug, "6e7781")
        r, g, b = (int(hexc[i:i + 2], 16) for i in (0, 2, 4))
        solid = Image.new("RGBA", raster.size, (r, g, b, 255))
        solid.putalpha(mask)
        solid = solid.resize((64, 64), Image.LANCZOS)
        solid.save(OUT / "icons" / f"{slug}.png")
        made.append(slug)
    print(f"icons: {len(made)}/{len(ICON_SLUGS)}")
    return made


def build_typing(theme, name):
    font = ImageFont.truetype(FONT, 28)
    w, h = 620, 56
    bg, fg = theme["bg"], theme["fg"]
    frames = []
    caret = "▌"
    for phrase in PHRASES:
        for n in range(0, len(phrase) + 1, 2):
            frames.append((phrase[:n], 45))
        for _ in range(6):
            frames.append((phrase, 150))
        for n in range(len(phrase), -1, -3):
            frames.append((phrase[:n], 25))
        frames.append(("", 150))
    built = []
    for text, dur in frames:
        im = Image.new("RGB", (w, h), bg)
        d = ImageDraw.Draw(im)
        line = text + caret
        tw = d.textlength(line, font=font)
        d.text(((w - tw) / 2, (h - 28) / 2 - 2), line, font=font, fill=fg)
        built.append((im.convert("P", palette=Image.ADAPTIVE, colors=16), dur))
    out = OUT / name
    built[0][0].save(out, save_all=True, append_images=[i for i, _ in built[1:]],
                     duration=[d for _, d in built], loop=0, optimize=True)
    print(f"{name}: {len(built)} frames, {out.stat().st_size // 1024} KB")


def build_stats(theme, name, counts, langs):
    w, h = 420, 250
    im = Image.new("RGB", (w, h), theme["bg"])
    d = ImageDraw.Draw(im)
    f_title = ImageFont.truetype(FONT_B, 19)
    f_body = ImageFont.truetype(FONT, 16)
    f_small = ImageFont.truetype(FONT, 13)
    d.rounded_rectangle([1, 1, w - 2, h - 2], 10, outline=theme["line"], width=1)
    d.text((22, 20), "GitHub Stats", font=f_title, fill=theme["fg"])
    rows = [("Commits", counts["commits"]), ("Repositories", counts["repos"]),
            ("Stars earned", counts["stars"]), ("Followers", counts["followers"])]
    y = 62
    for label, value in rows:
        d.text((22, y), label, font=f_body, fill=theme["muted"])
        d.text((w - 22, y), f"{value:,}", font=f_body, fill=theme["text"], anchor="ra")
        y += 27
    # Language bar
    top = [l for l in langs if l["bytes"] > 0][:5]
    total = sum(l["bytes"] for l in top) or 1
    bx, by, bw, bh = 22, y + 8, w - 44, 12
    palette = ["#a855f7", "#7952d3", "#3572A5", "#f1e05a", "#2f6fed"]
    x = bx
    for i, l in enumerate(top):
        seg = int(bw * l["bytes"] / total)
        d.rectangle([x, by, x + (seg if i == len(top) - 1 else seg - 2), by + bh],
                    fill=palette[i % len(palette)])
        x += seg
    ly = by + bh + 10
    legend = "  ".join(f"{l['name']} {100 * l['bytes'] / total:.0f}%" for l in top[:3])
    d.text((22, ly), legend, font=f_small, fill=theme["muted"])
    d.text((22, ly + 18), "  ".join(f"{l['name']} {100 * l['bytes'] / total:.0f}%" for l in top[3:5]),
           font=f_small, fill=theme["muted"])
    im.save(OUT / name)
    print(f"{name}: {im.size[0]}x{im.size[1]}")


def main():
    build_icons()
    build_typing(DARK, "typing-dark.gif")
    build_typing(LIGHT, "typing-light.gif")

    user = api(f"users/{USER}")
    repos = api(f"users/{USER}/repos?per_page=100")
    langs = repo_languages()
    counts = {
        "repos": user["public_repos"],
        "stars": sum(r["stargazers_count"] for r in repos),
        "followers": user["followers"],
    }
    # Commits: sum over the repos we actually own, via the contributor API.
    total_commits = 0
    for r in repos:
        if r["fork"]:
            continue
        try:
            stats = api(f"repos/{r['full_name']}/stats/contributors")
            total_commits += sum(c["total"] for c in stats if c.get("total"))
        except Exception:
            pass
    counts["commits"] = total_commits
    build_stats(DARK, "stats-dark.png", counts, langs)
    build_stats(LIGHT, "stats-light.png", counts, langs)


if __name__ == "__main__":
    main()
