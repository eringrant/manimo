# Native reveal.js export

A live `marimo run` deck ignores in-SVG fragments. For a shareable reveal.js deck
with true spacebar fragments, render the deck's **assets** (charts + diagrams) to
reveal-native files and package them. The helpers are in `manimo`.

## Render the assets

```python
from pathlib import Path

import altair as alt
from manim import DOWN, RIGHT, Arrow, Circle, Square, Text

from manimo import chart_html, render_svg_autoplay, render_svg_fragments

A = Path(__file__).parent / "reveal-assets"

# Altair chart -> interactive vega-embed fragment (vega from CDN; no Chrome needed)
data = alt.Data(values=[{"x": "a", "y": 3}, {"x": "b", "y": 1}, {"x": "c", "y": 2}])
chart = alt.Chart(data).mark_bar().encode(x="x:N", y="y:Q", tooltip=["x:N", "y:Q"])
chart_html(chart, A / "result.html")

# Manim diagram -> SVG. Each mobject in the list is one build-up step.
box = Square(color="#1f6feb").scale(0.8)
arrow = Arrow().next_to(box, RIGHT, buff=0.4)
ball = Circle(color="#1f6feb").next_to(arrow, RIGHT, buff=0.4)
label = Text("input -> output", font_size=22).next_to(box, DOWN, buff=0.7)

render_svg_fragments([box, arrow, ball, label], A / "mechanism.svg")  # steps on space
render_svg_autoplay([box, arrow, ball, label], A / "intuition.svg")   # CSS build-up
```

Build charts with `altair` straight from a `polars` DataFrame (`alt.Chart(df)`) or
inline `alt.Data(values=[...])`. `chart_html` writes them at a **fixed** pixel size
(`width`/`height`) — responsive `"container"` width measures 0 inside reveal slides.
The asset files are written when this code runs — put it in a chart/diagram cell, or
in a small script you run to regenerate `reveal-assets/`.

## Assemble the deck

`build_deck` packages the asset files into a reveal.js shell — reveal.js from CDN,
your brand color + font, and the autoplay-restart hook, all prewired.

```python
from pathlib import Path

from manimo import build_deck

# A is the reveal-assets dir from the previous step.
build_deck(
    [
        {"title": "Mechanism", "asset": A / "mechanism.svg"},
        {"title": "Intuition", "asset": A / "intuition.svg", "autoplay": True},
        {"title": "Result", "asset": A / "result.html"},
    ],
    Path("deck.html"),
    title="My deck",
    brand="#1f6feb",
    font='"Your Font", system-ui, sans-serif',
    google_fonts="https://fonts.googleapis.com/css2?family=Your+Font&display=swap",
)
```

Each `sections` entry is a dict:

| Key | Required | Meaning |
|---|---|---|
| `title` | no | `<h2>` heading for the section |
| `asset` | yes | path to an `.svg`/`.html` file (read inline), or raw HTML/markup |
| `autoplay` | no | `True` to restart a `render_svg_autoplay` SVG on each entry to the slide |

Signatures: `chart_html(chart, out, *, width=760, height=340)` and
`build_deck(sections, out, *, title=None, subtitle=None, brand="#1f6feb",
font="system-ui, sans-serif", google_fonts=None, transition="none")`. Charts inherit
their font/colors from `altair_theme` (set once); pass `brand`/`font` to `build_deck`
to match your theme, and for Manim text call `register_fonts(<dir>)` before building
`Text(font=...)`.
`build_deck` packages assets only — it doesn't reproduce arbitrary marimo cell
outputs (`mo.ui` widgets, tables), so render those as a chart or SVG first.

## Behavior in the exported deck

| Asset | Behavior |
|---|---|
| `chart_html` (Altair) | interactive (tooltips, pan/zoom), vector SVG |
| `render_svg_fragments` | steps on spacebar, reverses on back-nav |
| `render_svg_autoplay` | plays on entry (restarted by the hook `build_deck` wires) |

## Assembling by hand

To drop assets into your own reveal.js page, make each asset a `<section>`'s
content and wire the restart hook yourself:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5/dist/reveal.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5/dist/theme/white.css">
<div class="reveal"><div class="slides">
  <section><h2>Mechanism</h2><!-- paste reveal-assets/mechanism.svg --></section>
  <section class="autoplay"><h2>Intuition</h2><!-- paste reveal-assets/intuition.svg --></section>
  <section><h2>Result</h2><!-- paste reveal-assets/result.html --></section>
</div></div>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5/dist/reveal.js"></script>
<script>
  Reveal.initialize({ transition: 'none' });
  Reveal.on('slidechanged', e => {
    const a = e.currentSlide.querySelector('.autoplay');
    if (a) a.innerHTML = a.innerHTML;  // reparse -> restart the CSS animation
  });
</script>
```
