"""Rebuild the profile README.

Layout notes, each learned by breaking it once against GitHub's renderer:

* Cards sit two-per-row inside a single-line <p align="center">. A blank line anywhere
  inside that block closes it, and GitHub then renders each card as its own
  left-aligned paragraph — which is how the grid collapsed into one column.
* Not a <table>: GitHub's sanitizer drops <picture>/<source> inside table cells,
  which silently blanked every card.
* Social links are single badge images; inline <img> plus text cannot be trusted to
  align because each mark has different internal padding.
* Stack marks carry valign="middle" since inline images default to baseline.
"""
import pathlib

P = "https://a092devs.github.io/profile-assets/icons"
B = "https://a092devs.github.io/profile-assets/badges"
A = "https://raw.githubusercontent.com/a092devs/profile-assets/main/assets"

STACK = [
    ("kotlin", "Kotlin"), ("java", "Java"), ("cpp", "C++"), ("python", "Python"),
    ("fastapi", "FastAPI"), ("nodejs", "Node.js"), ("react", "React"),
    ("javascript", "JavaScript"), ("tailwindcss", "Tailwind CSS"),
    ("postgresql", "PostgreSQL"), ("docker", "Docker"), ("git", "Git"),
    ("linux", "Linux"),
]

CARDS = ["NexAlloyNext", "NexAlloyNext-Patches", "SystemFixes",
         "GameUnlocker", "OpsVista", "DataFoundry"]

HEIGHT = 42


def mark(key, label, themed=False):
    if themed:
        return (
            '<picture>'
            f'<source media="(prefers-color-scheme: dark)" srcset="{P}/{key}-dark.svg">'
            f'<source media="(prefers-color-scheme: light)" srcset="{P}/{key}.svg">'
            f'<img src="{P}/{key}.svg" height="{HEIGHT}" valign="middle" '
            f'alt="{label}" title="{label}" /></picture>'
        )
    return (f'<img src="{P}/{key}.svg" height="{HEIGHT}" valign="middle" '
            f'alt="{label}" title="{label}" />')


def card(name):
    return (
        f'<a href="https://github.com/a092devs/{name}"><picture>'
        f'<source media="(prefers-color-scheme: dark)" srcset="{A}/cards/{name}-dark.png">'
        f'<source media="(prefers-color-scheme: light)" srcset="{A}/cards/{name}-light.png">'
        f'<img src="{A}/cards/{name}-dark.png" width="47%" alt="{name}" />'
        f'</picture></a>'
    )


def row(*parts):
    """One HTML block, no blank lines, so the parts stay on the same line."""
    return '<p align="center">' + " &nbsp;&nbsp;&nbsp; ".join(parts) + "</p>"


card_rows = [row(*[card(n) for n in CARDS[i:i + 2]]) for i in range(0, len(CARDS), 2)]
stack_line = row(*[mark(k, l, themed=(k == "linux")) for k, l in STACK])

social_line = row(*[
    f'<a href="{href}"><img src="{B}/{name}.png" height="30" alt="{alt}" /></a>'
    for href, name, alt in [
        ("https://www.linkedin.com/in/a092devs", "linkedin", "LinkedIn"),
        ("https://twitter.com/a092devs", "x", "X"),
        ("mailto:arsalanakhtar0@gmail.com", "envelope-src", "Email"),
    ]
])

banner = (
    '<picture>'
    f'<source media="(prefers-color-scheme: dark)" srcset="{A}/typing-dark.gif">'
    f'<source media="(prefers-color-scheme: light)" srcset="{A}/typing-light.gif">'
    f'<img src="{A}/typing-dark.gif" alt="Android, web and data work" width="620" />'
    '</picture>'
)

stats = (
    '<picture>'
    f'<source media="(prefers-color-scheme: dark)" srcset="{A}/stats-dark.png">'
    f'<source media="(prefers-color-scheme: light)" srcset="{A}/stats-light.png">'
    f'<img src="{A}/stats-dark.png" alt="GitHub stats" width="420" />'
    '</picture>'
)

doc = f"""<div align="center">

# Hi, I'm Arsalan \U0001f44b

{banner}

{social_line}

</div>

---

I've always wanted to know where a decision actually gets made. In Android that's
usually a layer below the app — a module, a patch, a flag in a config file nobody
documented. On the web it's the database quietly disagreeing with the dashboard built
on top of it. Most of what I do is reading code I didn't write and getting it to behave.

---

### \U0001f31f Selected work

{chr(10).join(card_rows)}

{row('<a href="https://github.com/a092devs?tab=repositories">The rest of it lives in the repository list</a>')}

---

### \U0001f6e0\ufe0f Stack

{stack_line}

---

<div align="center">

{stats}

</div>
"""

pathlib.Path("profile_README.md").write_text(doc, encoding="utf-8")
b = doc.encode("utf-8")
print("bytes:", len(b), "| backslashes:", b.count(bytes([92])))
print("card rows:", len(card_rows), "| marks:", doc.count(f'{P}/'), "| badges:", doc.count(f"{B}/"))
print("blank lines inside any <p>:", doc.count("<p align=\"center\">\n\n"))
