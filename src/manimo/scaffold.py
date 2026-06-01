"""Drop the bundled theme and a runnable starter deck into a consumer's project.

``manimo`` is meant to be ADDED to your project and imported, not cloned.
But marimo resolves a notebook's ``css_file`` / ``html_head_file`` relative to the
notebook, so the theme files have to live next to it. ``init_deck`` writes a
minimal, runnable deck (notebook + layout + theme) into your own directory, so
``uv add manimo`` is enough to get started.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

THEME_FILES = ("_slide_theme.css", "_slide_head.html")


def _copy_theme(dest: str | Path, *, overwrite: bool = False) -> list[Path]:
  """Copy the bundled theme files into ``dest`` (next to the deck notebook).

  Copies ``_slide_theme.css`` and ``_slide_head.html`` — the files a deck's
  ``marimo.App(css_file=..., html_head_file=...)`` points at. marimo resolves
  those paths relative to the notebook, so they must sit in the same directory.
  Existing files are left untouched unless ``overwrite=True``. Returns the paths
  written.
  """
  from . import THEME_DIR  # local import to avoid a cycle at module load

  dest = Path(dest)
  dest.mkdir(parents=True, exist_ok=True)
  written: list[Path] = []
  for name in THEME_FILES:
    target = dest / name
    if target.exists() and not overwrite:
      continue
    shutil.copy(THEME_DIR / name, target)
    written.append(target)
  return written


def init_deck(dest: str | Path, *, name: str = "main", overwrite: bool = False) -> Path:
  """Scaffold a runnable starter slide deck in ``dest`` and return its notebook path.

  Writes ``<name>.py`` (a marimo slides notebook with a title slide, a Manim
  build-up diagram, and an interactive Altair chart), ``layouts/<name>.slides.json``
  (the slide layout), and copies the bundled theme next to it. Present it with
  ``marimo run <dest>/<name>.py`` or edit it with ``marimo edit``. Refuses to
  clobber an existing notebook unless ``overwrite=True``.
  """
  dest = Path(dest)
  (dest / "layouts").mkdir(parents=True, exist_ok=True)
  _copy_theme(dest, overwrite=overwrite)

  notebook = dest / f"{name}.py"
  if notebook.exists() and not overwrite:
    raise FileExistsError(f"{notebook} exists (pass overwrite=True to replace)")
  notebook.write_text(_starter_notebook(name))
  (dest / "layouts" / f"{name}.slides.json").write_text(_starter_layout())
  return notebook


def _starter_notebook(name: str) -> str:
  """Return the source of a minimal, runnable marimo slides notebook."""
  try:
    import marimo

    version = marimo.__version__
  except Exception:  # pragma: no cover - marimo is a core dep, but stay defensive
    version = "0.18.4"
  title = (
    "Untitled deck"
    if name == "main"
    else name.replace("_", " ").replace("-", " ").title()
  )
  return f'''import marimo

__generated_with = "{version}"
app = marimo.App(
    width="medium",
    layout_file="layouts/{name}.slides.json",
    css_file="_slide_theme.css",
    html_head_file="_slide_head.html",
    app_title="{title}",
)


@app.cell
def _():
    import marimo as mo

    return (mo,)


# Setup (skip): render a Manim diagram to a self-contained build-up SVG. Manim is
# a core dependency; rendering needs system cairo + pango (no ffmpeg). The diagram
# loops in the editor "view as slides" preview and plays once (restarting on slide
# entry via the bundled _slide_head.html hook) under `marimo run`.
@app.cell
def _(mo):
    from pathlib import Path

    from manim import DOWN, RIGHT, Arrow, Circle, Square, Text

    from manimo import render_svg_autoplay, svg_image

    _box = Square(color="#1f6feb").scale(0.8)
    _arrow = Arrow().next_to(_box, RIGHT, buff=0.4)
    _ball = (
        Circle(color="#1f6feb")
        .set_fill("#1f6feb", 0.3)
        .scale(0.8)
        .next_to(_arrow, RIGHT, buff=0.4)
    )
    _label = Text("input -> mechanism -> output", font_size=22).next_to(
        _box, DOWN, buff=0.7
    )
    _mode = mo.app_meta().mode or "static"
    diagram = render_svg_autoplay(
        [_box, _arrow, _ball, _label],  # one build-up step per item
        Path(__file__).parent / "assets" / f"{name}_diagram_{{_mode}}.svg",
        loop=_mode == "edit",
    )
    return diagram, svg_image


# Slide 1 (title). The two cells above are "skip" in the layout, so they run but
# never become slides; each cell below maps positionally to one slide entry.
@app.cell
def _(mo):
    mo.md(
        """
        # {title}

        ### A reveal.js deck, live from a marimo notebook

        Press **Space** / arrow keys to advance.
        """
    )
    return


# Slide 2: the Manim diagram, inlined so reveal.js can animate it.
@app.cell
def _(diagram, mo, svg_image):
    mo.vstack([mo.md("## A Manim diagram"), svg_image(diagram)])
    return


# Slide 3: an interactive Altair chart.
@app.cell
def _(mo):
    import altair as alt

    _data = alt.Data(values=[{{"x": i, "y": i * i}} for i in range(10)])
    _chart = (
        alt.Chart(_data)
        .mark_line(point=True)
        .encode(x="x:Q", y="y:Q", tooltip=["x:Q", "y:Q"])
        .properties(height=320, title="y = x squared")
    )
    mo.vstack([mo.md("## An interactive chart"), mo.center(mo.ui.altair_chart(_chart))])
    return


if __name__ == "__main__":
    app.run()
'''


def _starter_layout() -> str:
  """Return a slides layout: two skipped setup cells + three slides."""
  layout = {
    "type": "slides",
    "data": {
      "deck": {"transition": "none"},
      "cells": [
        {"type": "skip"},
        {"type": "skip"},
        {"type": "slide"},
        {"type": "slide"},
        {"type": "slide"},
      ],
    },
  }
  return json.dumps(layout, indent=2) + "\n"
