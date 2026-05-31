# Manim graphics in slides

Slides can embed [Manim](https://www.manim.community) graphics — a mechanism, an
algorithm step-by-step, a training dynamic. Everything here is a **vector SVG
diagram** (crisp, tiny, no ffmpeg): reveal it in fragments (`render_svg_fragments`)
or as a self-contained CSS build-up (`render_svg_autoplay`).

## A vector SVG diagram, revealed in fragments

`manimo` gives you `render_svg_fragments` (compose a list of
mobjects into one SVG where each is a reveal.js fragment), `render_svg_autoplay`
(one SVG that builds up on its own via CSS), and `svg_image` (inline + center it
on the slide). SVG is vector — crisp at any projector size, tiny, and needs no
ffmpeg. A single SVG can't hold continuous motion, but reveal.js **fragments** let
the diagram build up piece by piece.

Do the build/render in a cell marked `skip`, then display in the slide cell:

```python
@app.cell
def _make_diagram():
    from pathlib import Path
    from manim import DOWN, RIGHT, Arrow, Circle, Square, Text
    from manimo import render_svg_fragments, svg_image

    box = Square(color="#1f6feb").scale(0.8)
    arrow = Arrow().next_to(box, RIGHT, buff=0.4)
    ball = Circle(color="#1f6feb").set_fill("#1f6feb", 0.3).scale(0.8).next_to(arrow, RIGHT, buff=0.4)
    label = Text("input → mechanism → output", font_size=22).next_to(box, DOWN, buff=0.7)
    svg = render_svg_fragments(
        [box, arrow, ball, label],            # one reveal step per item
        Path(__file__).parent / "assets" / "diagram.svg",
    )
    return svg, svg_image

@app.cell
def diagram_slide(mo, svg, svg_image):
    mo.vstack([mo.md("## Intuition, in fragments"), svg_image(svg)])
    return
```

`svg_image` **inlines** the SVG into the slide DOM (not an `<img>`) so reveal.js
can see and step the `.fragment` groups. In `render_svg_fragments` the first part
shows immediately and each later part reveals on advance.

## Fragments vs. autoplay (which one when)

A single SVG can't hold continuous motion, but it can build up. Two helpers:

- **`render_svg_fragments(parts, out)`** — each part is a reveal.js `.fragment`.
  Steps on **spacebar** in a *native* reveal.js export (see [`REVEAL.md`](REVEAL.md)).
  marimo's run-mode reveal ignores in-SVG fragments, so there it shows everything
  at once — use autoplay for live marimo.
- **`render_svg_autoplay(parts, out, *, stagger=0.7, dur=0.5, loop=False, hold=10)`**
  — one self-contained SVG that fades the parts in via CSS, no spacebar needed.
  - `loop=False` (default): plays the build-up **once** when the SVG is first
    rendered. Because a deck pre-renders all slides, it can finish before you
    navigate in — so the bundled `_slide_head.html` (run mode) and `build_deck`
    both wire a `slidechanged` hook that **restarts it on slide entry**.
  - `loop=True`: repeats forever (build up → hold `hold` seconds → reset). Pure
    CSS with no entry trigger, so it animates **everywhere** — including marimo's
    editor "view as slides" preview, where head/cell scripts don't run — at the
    cost of replaying on a timer rather than precisely on entry.

A common pattern is to pick the mode from the runtime so the editor preview loops
but `marimo run` gets the crisp entry-triggered build-up:

```python
mode = mo.app_meta().mode or "static"
diagram = render_svg_autoplay(parts, f"assets/diagram_{mode}.svg", loop=mode == "edit")
```

## Tips

- Colors are baked into the SVG at render time — set mobject colors to your theme
  palette (e.g. the `--brand` hex) so graphics are on-brand.
- `Text` needs no LaTeX (Pango). `Tex`/`MathTex` need a LaTeX install and render
  **empty with no error** if it's missing — check `uv run manim checkhealth`.
- Import every manim name you use (incl. direction constants like `UP`/`RIGHT`),
  or you'll get a `NameError` at render.
- The default Cairo renderer is headless-safe; don't use the OpenGL renderer here.
