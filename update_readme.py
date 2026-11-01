"""Rebuild the two icon blocks in the profile README from the files actually present
in docs/icons, so the markup can never drift from what is deployed.

Marks keep their intrinsic aspect ratio (height only is set), and Linux and X go through
<picture> because their official artwork is drawn in black and needs a light copy for the
dark theme.
"""
import json
import pathlib
import re
import subprocess

P = "https://a092devs.github.io/profile-assets/icons"

LABELS = {
    "kotlin": "Kotlin", "java": "Java", "cpp": "C++", "python": "Python",
    "fastapi": "FastAPI", "nodejs": "Node.js", "react": "React",
    "javascript": "JavaScript", "tailwindcss": "Tailwind CSS",
    "postgresql": "PostgreSQL", "docker": "Docker", "git": "Git", "linux": "Linux",
}
ORDER = ["kotlin", "java", "cpp", "python", "fastapi", "nodejs", "react",
         "javascript", "tailwindcss", "postgresql", "docker", "git", "linux"]
H = 42


def img(key, height=H):
    return (f'<img src="{P}/{key}.svg" height="{height}" '
            f'alt="{LABELS.get(key, key)}" title="{LABELS.get(key, key)}" />')


def themed(key, label, height=H):
    return (
        f'<picture><source media="(prefers-color-scheme: dark)" srcset="{P}/{key}-dark.svg">'
        f'<source media="(prefers-color-scheme: light)" srcset="{P}/{key}.svg">'
        f'<img src="{P}/{key}.svg" height="{height}" alt="{label}" title="{label}" /></picture>'
    )


stack = '<div align="center">\n\n' + "\n".join(
    themed("linux", "Linux") if k == "linux" else img(k) for k in ORDER
) + "\n\n</div>"

social = " ".join([
    f'<a href="https://www.linkedin.com/in/a092devs">{img("linkedin", 24)}'
    f'&nbsp;<b>LinkedIn</b></a>',
    f'<a href="https://twitter.com/a092devs">{themed("x", "X", 24)}&nbsp;<b>X</b></a>',
    f'<a href="mailto:arsalanakhtar0@gmail.com">{img("gmail", 24)}&nbsp;<b>Email</b></a>',
])

# Start from whatever is live so the project cards and prose are not retyped by hand.
live = subprocess.run(
    ["gh", "api", "repos/a092devs/a092devs/contents/README.md", "--jq", ".content"],
    capture_output=True, text=True, check=True).stdout
s = pathlib.Path("profile_README.md").resolve()

import base64
s.write_text(base64.b64decode(live).decode("utf-8"), encoding="utf-8")
txt = s.read_text(encoding="utf-8")

# Replace the social line (the single long line holding the LinkedIn anchor).
lines = txt.split("\n")
for i, ln in enumerate(lines):
    if "linkedin" in ln and "<a href=" in ln:
        lines[i] = social
        break
else:
    raise SystemExit("social line not found")
txt = "\n".join(lines)

# Replace the Stack block.
start = txt.index("### 🛠️ Stack")
end = txt.index("\n</div>", start) + len("\n</div>")
txt = txt[:start] + "### 🛠️ Stack\n\n" + stack + txt[end:]

s.write_text(txt, encoding="utf-8")
print("stack imgs:", len(re.findall(r"<img ", stack)), "| bytes:", len(txt))
print("picture blocks:", txt.count("<picture>"))
