"""Builds the GitHub profile assets locally: brand icons, an animated typing
banner, and the stats cards. Everything is emitted as PNG or GIF because GitHub
serves repo-hosted SVG as text/plain, which breaks <img>.
"""
import io
import json
import math
import subprocess
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

OUT = Path(__file__).parent / "assets"

USER = "a092devs"
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


UI_FONT = find_font("segoeui.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf")
UI_FONT_B = find_font("segoeuib.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf")

LANG_COLORS = {
    "kotlin": "#a855f7", "java": "#b07219", "python": "#3572a5",
    "javascript": "#f1e05a", "css": "#563d7c", "c++": "#f34b7d",
    "html": "#e34c26", "typescript": "#3178c6", "shell": "#89e051",
}

CARD_REPOS = ["NexAlloyNext", "NexAlloyNext-Patches", "SystemFixes",
              "OpsVista", "DataFoundry", "GameUnlocker"]


def build_cards():
    """Repo cards in GitHub's pinned-card style, one dark and one light variant."""
    (OUT / "cards").mkdir(exist_ok=True)
    W, H = 820, 260
    title_f = ImageFont.truetype(UI_FONT_B, 32)
    desc_f = ImageFont.truetype(UI_FONT, 24)
    meta_f = ImageFont.truetype(UI_FONT, 22)
    themes = {"dark": dict(bg="#0d1117", border="#30363d", title="#58a6ff",
                           desc="#8b949e", meta="#7d8590", dot_fg="#c9d1d9"),
              "light": dict(bg="#ffffff", border="#d0d7de", title="#0969da",
                            desc="#57606a", meta="#656d76", dot_fg="#1f2328")}
    made = []
    for name in CARD_REPOS:
        try:
            info = api(f"repos/{USER}/{name}")
        except Exception as exc:
            print(f"  ! card {name}: {exc}")
            continue
        desc = (info.get("description") or "").strip()
        lang = info.get("language") or ""
        stars = info.get("stargazers_count", 0)
        forks = info.get("forks_count", 0)
        for theme, c in themes.items():
            im = Image.new("RGB", (W, H), c["bg"])
            d = ImageDraw.Draw(im)
            d.rounded_rectangle([1, 1, W - 2, H - 2], 14, outline=c["border"], width=2)
            d.text((34, 30), name, font=title_f, fill=c["title"])
            # wrap description to three lines
            words, lines, cur = desc.split(), [], ""
            for wd in words:
                trial = (cur + " " + wd).strip()
                if d.textlength(trial, font=desc_f) > W - 76:
                    lines.append(cur); cur = wd
                else:
                    cur = trial
            if cur:
                lines.append(cur)
            y = 92
            for ln in lines[:3]:
                d.text((34, y), ln, font=desc_f, fill=c["desc"])
                y += 34
            if len(lines) > 3:
                d.text((34, y - 6), "...", font=desc_f, fill=c["desc"])
            mx = 34
            my = H - 56
            if lang:
                d.ellipse([mx, my + 5, mx + 15, my + 20],
                          fill=LANG_COLORS.get(lang.lower(), "#8b949e"))
                d.text((mx + 24, my), lang, font=meta_f, fill=c["meta"])
                mx += 24 + d.textlength(lang, font=meta_f) + 34
            for icon, val in ((_star, stars), (_fork, forks)):
                mx = icon(d, mx, my + 10, c["meta"])
                d.text((mx + 8, my), str(val), font=meta_f, fill=c["meta"])
                mx += d.textlength(str(val), font=meta_f) + 30
            im.save(OUT / "cards" / f"{name}-{theme}.png")
            made.append(f"{name}-{theme}")
    print(f"cards: {len(made)}")
    return made


def _star(d, x, cy, color):
    """Drawn rather than typed: the meta font has no reliable star codepoint."""
    r = 8.0
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((x + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=color)
    return x + 2 * r


def _fork(d, x, cy, color):
    r = 3.4
    for dy in (-7, 7):
        d.ellipse([x + 4 - r, cy + dy - r, x + 4 + r, cy + dy + r], outline=color, width=2)
    d.line([x + 4, cy - 4, x + 4, cy + 4], fill=color, width=2)
    d.line([x + 4, cy, x + 14, cy], fill=color, width=2)
    d.line([x + 14, cy - 7, x + 14, cy + 7], fill=color, width=2)
    return x + 20


def main():
    build_cards()
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
