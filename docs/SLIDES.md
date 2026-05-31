# Presenting a marimo notebook as slides

A marimo notebook can be presented as a [reveal.js](https://revealjs.com) deck
using marimo's [slides layout](https://docs.marimo.io/guides/apps/#slides-layout).
`manimo` ships a shared 16:9 slide theme so every deck looks consistent and fits
the frame.

## Fastest path: scaffold a deck

```bash
uv run python -m manimo init mydeck     # writes mydeck/main.py + layout + theme
uv run marimo run mydeck/main.py
```

That gives you a working deck to edit. The rest of this doc explains what `init`
sets up, in case you're wiring an existing notebook by hand.

## The theme files

`manimo` bundles two files (find them at `manimo.THEME_DIR`):

| File | Purpose |
|---|---|
| `_slide_theme.css` | Base theme: fonts, color variables, the 16:9 output-sizing guard. Rebrand by editing its variables (see the README's Theme section). |
| `_slide_head.html` | Injected into the deck `<head>` in **run mode**. Loads default fonts, and carries a small script that **restarts `render_svg_autoplay` SVGs on slide entry** (see [`ANIMATIONS.md`](ANIMATIONS.md)). |

marimo resolves `css_file` / `html_head_file` **relative to the notebook file**,
so these must sit next to your `main.py`. `manimo init` puts them there; to wire a
notebook by hand, copy them from `THEME_DIR`:

```bash
THEME=$(uv run python -c 'import manimo; print(manimo.THEME_DIR)')
cp "$THEME"/_slide_theme.css "$THEME"/_slide_head.html mydeck/
```

## Wiring a notebook to slides

In the notebook's `marimo.App(...)` call:

```python
app = marimo.App(
    width="medium",
    layout_file="layouts/main.slides.json",
    css_file="_slide_theme.css",          # in the same dir as the notebook
    html_head_file="_slide_head.html",    # same dir; carries the autoplay hook
    app_title="My deck",
)
```

The layout file is plain JSON and can be committed without opening the GUI:

```json
{
  "type": "slides",
  "data": {
    "deck": { "transition": "none" },
    "cells": [
      { "type": "skip" },
      { "type": "slide" },
      { "type": "fragment" },
      { "type": "slide" }
    ]
  }
}
```

The `cells` array maps **positionally** to the notebook's cells, in source order,
including setup cells — so it must have one entry per cell, and the first entry
typically `skip`s the imports cell. Each `type`:

| `type` | Effect |
|---|---|
| `slide` | starts a new slide |
| `fragment` | reveals on the **same** slide as the preceding cell |
| `sub-slide` | a vertical sub-slide |
| `skip` | runs the cell but keeps it out of the deck (imports, data loading, renders) |

For a concrete notebook-to-layout pairing to copy, run `python -m manimo init`
and read the generated `main.py` alongside its `layouts/main.slides.json`.

> **Transition is `none` on purpose.** reveal.js defaults to a horizontal *swipe*
> (`"slide"`), which is distracting for technical content; instant cuts read
> better. See marimo issue [#9700](https://github.com/marimo-team/marimo/issues/9700).

## Keeping output inside the frame

The theme caps every cell output at `--slide-output-max-h` (72vh) and scrolls
the overflow, so a big dataframe or wide plot can't blow out the slide. Still,
design slides to show *one idea*: prefer `mo.hstack`/`mo.vstack` to compose,
downsample big tables (`df.head(8)`), and mark heavy setup cells `"skip"`.

## Presenting

```bash
uv run marimo run mydeck/main.py     # live reveal.js deck (run mode)
uv run marimo edit mydeck/main.py    # edit as a notebook; switch to the slides view to preview

# serve on a fixed host/port without opening a browser (e.g. to share):
uv run marimo run mydeck/main.py --headless --host 127.0.0.1 --port 8800
```

`marimo run` is the real presentation mode (it injects `_slide_head.html`); the
editor's "view as slides" is a preview that does not. The `--headless`/`--host`/
`--port` flags are marimo's; see `uv run marimo run --help` for the full set.

## Animations

Slides can embed Manim diagrams. See [`ANIMATIONS.md`](ANIMATIONS.md) for the
vector-SVG helpers: `render_svg_fragments` steps on spacebar in a native reveal.js
export ([`REVEAL.md`](REVEAL.md)), while `render_svg_autoplay` plays on display in
live marimo (which ignores in-SVG fragments).
