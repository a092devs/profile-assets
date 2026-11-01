Assets for my [profile README](https://github.com/a092devs/a092devs).

`build_assets.py` generates the banner, icons and stats card. A nightly workflow
reruns it and commits the result, so the profile just picks up fresh numbers.

Everything is PNG or GIF on purpose — GitHub serves repo SVGs as `text/plain`,
which means they won't render as images in a README.
