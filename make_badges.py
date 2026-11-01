"""Generate self-contained social badges: brand tile, official mark, and the label
all inside one image.

Inline <img> + text cannot be relied on to align in GitHub markdown — the marks have
different internal padding, so LinkedIn's tile looked small next to X and Gmail. Baking
the label into the image removes the problem entirely.
"""
import io
import pathlib

from PIL import Image, ImageDraw, ImageFont
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

SRC = pathlib.Path("docs/icons")
DST = pathlib.Path("docs/badges")
DST.mkdir(parents=True, exist_ok=True)

H = 40
PAD = 6
FONT_B = pathlib.Path("C:/Windows/Fonts/segoeuib.ttf")
if not FONT_B.exists():
    FONT_B = pathlib.Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
LABEL_FONT = ImageFont.truetype(str(FONT_B), 19)

BADGES = [
    ("linkedin", "LinkedIn", "0A66C2"),
    ("x", "X", "18181B"),
    ("_envelope-src", "Email", "EA4335"),
]


def raster(name, box):
    """Render an SVG mark and return its silhouette as a greyscale mask."""
    d = svg2rlg(str(SRC / f"{name}.svg"))
    s = 200.0 / max(d.width, d.height)
    d.scale(s, s)
    d.width, d.height = d.width * s, d.height * s
    buf = io.BytesIO()
    renderPM.drawToFile(d, buf, fmt="PNG")
    buf.seek(0)
    img = Image.open(buf).convert("RGBA")
    alpha = img.getchannel("A")
    mask = alpha if alpha.getextrema()[0] < 250 else img.convert("L").point(lambda v: 255 - v)
    return mask.crop(mask.getbbox())


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


for name, label, colour in BADGES:
    mark = raster(name, None)
    inner = H - 2 * PAD - 6
    fit = inner / max(mark.size)
    mark = mark.resize((max(1, int(mark.width * fit)), max(1, int(mark.height * fit))),
                       Image.LANCZOS)

    probe = ImageDraw.Draw(Image.new("L", (8, 8)))
    lw = int(probe.textlength(label, font=LABEL_FONT)) + 30
    w = H + lw

    img = Image.new("RGBA", (w, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, H - 1], radius=8, fill=(36, 41, 46, 255))
    d.rounded_rectangle([0, 0, H * 2 - 1, H - 1], radius=8, fill=(*hexrgb(colour), 255))
    d.rectangle([H, 0, H * 2, H - 1], fill=(*hexrgb(colour), 255))

    white = Image.new("RGBA", mark.size, (255, 255, 255, 255))
    img.paste(white, ((H - mark.width) // 2, (H - mark.height) // 2), mark)
    d.text((H + 15, H / 2), label, font=LABEL_FONT, fill=(245, 247, 250, 255), anchor="lm")

    img.save(DST / f"{name}.png")
    print(f"{name:10} {w}x{H}")
