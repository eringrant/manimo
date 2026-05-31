# `manimo`

Turn [marimo](https://marimo.io) notebooks with [manim](https://www.manim.community/) 
into [reveal.js](https://revealjs.com) slide decks: `manimo` = `marimo` + `manim`.

## Install

Add `manimo` as a Git dependency:

```bash
uv add "manimo @ git+https://github.com/eringrant/manimo-slides"
```

Manim is a core dependency. Rendering its diagrams also needs the system libraries
**cairo** and **pango** (LaTeX only for `Tex`/`MathTex`). On macOS:

```bash
brew install cairo pango pkg-config
uv run manim checkhealth     # verify the toolchain (answer N to the preview prompt)
```

## Quickstart

```bash
uv run python -m manimo init mydeck     # writes mydeck/ : main.py + layout + theme
uv run marimo run mydeck/main.py        # present it (reveal.js)
uv run marimo edit mydeck/main.py       # or edit it as a notebook
```

`init` writes a deck with a title slide, a Manim build-up diagram, and a Plotly
chart, the slide-layout JSON, and the bundled theme. marimo resolves a notebook's
`css_file` / `html_head_file` relative to the notebook, so the theme files sit next
to `main.py`.

## Theme

`manimo init` places two files next to your notebook: `_slide_theme.css` (the
styles) and `_slide_head.html` (a `<head>` snippet that loads fonts and restarts
autoplay diagrams on slide entry). To wire a deck by hand, copy them from
`THEME_DIR` (see [`docs/SLIDES.md`](docs/SLIDES.md)).

Rebrand by editing the variables at the top of `_slide_theme.css`.
Put overrides in that one file; a relative `@import` won't work,
because marimo inlines the CSS and serves no sibling files.

| Variable | Owner | Controls |
|---|---|---|
| `--brand`, `--brand-accent`, `--brand-fg`, `--brand-bg`, `--brand-muted` | manimo | colors (headings, links, text, background) |
| `--brand-logo`, `--brand-logo-w/h` | manimo | optional corner logo |
| `--slide-output-max-h` | manimo | per-output height cap (16:9 guard) |
| `--marimo-heading-font`, `--marimo-text-font`, `--marimo-monospace-font` | marimo | fonts (the theme sets these to a system stack) |

## API

Everything is importable from the top level (`from manimo import ...`). A deck is
either **live** (served by `marimo run`) or a **reveal** export (a standalone
`deck.html` built by `build_deck`); the last column says where each function applies.

### Scaffold

| Function | Purpose |
|---|---|
| `init_deck(dir, *, name="main")` | write a runnable deck — notebook + layout + theme (also `python -m manimo init <dir>`) |
| `THEME_DIR` | `Path` to the bundled theme files, for wiring a deck by hand |

### Diagrams — Manim mobjects → vector SVG

| Function | Purpose | Target |
|---|---|---|
| `render_svg_autoplay(parts, out, *, loop=False, hold=10)` | build up the parts via a CSS animation | live + reveal |
| `render_svg_fragments(parts, out)` | reveal each part on a spacebar press | reveal |
| `register_fonts(dir)` | register `.ttf`/`.otf` fonts before building Manim `Text` | live + reveal |

### Display & assembly

| Function | Purpose | Target |
|---|---|---|
| `svg_image(src, *, max_width=760)` | inline an SVG into a marimo cell | live |
| `figure_html(fig, out, *, font=None)` | a Plotly figure → an interactive HTML asset | reveal |
| `build_deck(sections, out, *, title=, brand=, font=, google_fonts=)` | package assets into a standalone `deck.html` | reveal |

In a live deck, charts are marimo's own `mo.ui.plotly`; `figure_html` is only for a
reveal export. `render_svg_fragments` is reveal-only because live marimo ignores
in-SVG fragments.

## Docs

- [`docs/SLIDES.md`](docs/SLIDES.md) — wiring a notebook to the slides layout
- [`docs/REVEAL.md`](docs/REVEAL.md) — native reveal.js export
- [`docs/ANIMATIONS.md`](docs/ANIMATIONS.md) — Manim diagrams

## Related projects

- [marimo](https://marimo.io) — the reactive Python notebook manimo builds on.
- [Manim](https://www.manim.community/) — the engine behind the vector diagrams.
- [reveal.js](https://revealjs.com) — the framework the decks render to.
- [Plotly](https://plotly.com/python/) — interactive charts (`figure_html`).
- [manim-slides](https://github.com/jeertmans/manim-slides) — a separate, unrelated project: slideshows built from Manim.

## AI Usage

All code and documentation written by @claude with orchestration by @eringrant.

## License

MIT
