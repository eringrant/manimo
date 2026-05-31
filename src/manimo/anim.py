"""Render Manim diagrams to vector SVG for embedding in marimo slide decks.

Rendering needs Manim's system libraries cairo + pango (and LaTeX *only* for
`Tex`/`MathTex`); see the README for setup. No ffmpeg is needed — everything here
is vector SVG.

Diagrams are vector (crisp at any projector size, tiny). A single SVG can't hold
continuous motion, but it can build up piece by piece: `render_svg_fragments`
emits reveal.js `.fragment`s that step on spacebar in a native reveal deck, and
`render_svg_autoplay` emits a self-contained CSS build-up that plays on display.

manim is imported lazily inside the functions, so importing the package stays cheap
despite manim being a heavy dependency.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
  import marimo

_REGISTERED_DIRS: set[str] = set()


def register_fonts(directory: str | Path) -> None:
  """Register every .ttf/.otf in ``directory`` with Pango (idempotent, best-effort).

  Call this BEFORE constructing ``Text(font="...")`` — Manim lays out glyphs to
  vector paths at construction, so the font must be registered first. manimo ships
  no fonts of its own; point this at wherever your font files live. No-op if
  manimpango isn't installed or the directory is missing.
  """
  directory = Path(directory)
  key = str(directory.resolve()) if directory.exists() else str(directory)
  if key in _REGISTERED_DIRS or not directory.is_dir():
    return
  _REGISTERED_DIRS.add(key)
  try:
    import manimpango  # lazy

    for f in sorted([*directory.glob("*.ttf"), *directory.glob("*.otf")]):
      manimpango.register_font(str(f))
  except Exception:
    pass


def _invisible_frame(parts: Sequence[Any]) -> Any:
  """An invisible bounding rectangle around ``parts`` (with padding).

  Sharing one frame across per-part renders gives every SVG the same viewBox, so
  the parts stay aligned when revealed one at a time.
  """
  from manim import Rectangle  # lazy
  from manim import VGroup  # lazy

  full = VGroup(*parts)
  return Rectangle(
    width=max(full.width, 0.1) + 1.0,
    height=max(full.height, 0.1) + 1.0,
    stroke_opacity=0,
    fill_opacity=0,
  ).move_to(full.get_center())


def _svg_layers(parts: Sequence[Any]) -> tuple[str, list[str]]:
  """Render each part on the shared invisible frame, one SVG at a time.

  Returns the opening ``<svg ...>`` tag and each part's inner markup, leaving the
  caller to wrap each layer as it needs (a reveal fragment, an animated group, ...).
  """
  import re
  import tempfile

  from manim import VGroup  # lazy
  from manim_mobject_svg import create_svg_from_vmobject  # lazy

  frame = _invisible_frame(parts)
  header = ""
  inners: list[str] = []
  with tempfile.TemporaryDirectory() as tmpdir:
    for i, part in enumerate(parts):
      tmp = Path(tmpdir, f"part_{i}.svg")
      create_svg_from_vmobject(VGroup(frame.copy(), part), str(tmp))
      svg = tmp.read_text()
      if not header:
        match = re.search(r"<svg[^>]*>", svg)
        header = match.group(0) if match else ""
      inners.append(svg[svg.index(">", svg.index("<svg")) + 1 : svg.rindex("</svg>")])
  return header, inners


def render_svg_autoplay(
  parts: Sequence[Any],
  out: str | Path,
  *,
  stagger: float = 0.7,
  dur: float = 0.5,
  loop: bool = False,
  hold: float = 10.0,
) -> Path:
  """Compose ``parts`` into ONE self-contained SVG that AUTO-PLAYS a build-up.

  Each part fades in in sequence via CSS ``@keyframes`` (staggered
  ``animation-delay``). Vector, no video, no control — it plays on its own when
  the SVG is shown. Parts share an invisible frame so they align. Display with
  ``svg_image`` (inline).

  ``loop=False`` (default) plays the build-up ONCE when the SVG is first
  rendered; if a deck pre-renders all slides it may finish before you navigate in
  (use the ``slidechanged`` reparse hook that ``build_deck`` / the bundled
  ``_slide_head.html`` wire up to restart it on entry).

  ``loop=True`` instead repeats forever: the parts build up, hold for ``hold``
  seconds, then reset and replay. Because it is pure CSS with no entry trigger, it
  animates in EVERY context — including marimo's editor "view as slides" preview,
  where head scripts and cell scripts don't run — at the cost of replaying on a
  timer rather than precisely on slide entry.
  """
  out = Path(out)
  out.parent.mkdir(parents=True, exist_ok=True)

  header, inners = _svg_layers(parts)
  if loop:
    # One infinite keyframe per layer over a shared cycle (build-up, then hold,
    # then reset): each layer stays invisible until its slot, fades in over
    # ``dur``, and holds to the end of the cycle before the loop resets it.
    build_end = (len(inners) - 1) * stagger + dur if inners else dur
    cycle = build_end + hold
    styles, layers = [], []
    for i, inner in enumerate(inners):
      start_pct = 100 * (i * stagger) / cycle
      end_pct = 100 * (i * stagger + dur) / cycle
      name = f"svgfade{i}"
      styles.append(
        f"@keyframes {name}{{0%,{start_pct:.2f}%{{opacity:0}}"
        f"{end_pct:.2f}%,100%{{opacity:1}}}}"
      )
      layers.append(
        f'<g style="opacity:0;animation:{name} {cycle:.2f}s linear infinite">'
        f"{inner}</g>"
      )
    style = "<style>" + "".join(styles) + "</style>"
  else:
    layers = [
      f'<g style="opacity:0;animation:svgfade {dur}s ease forwards;'
      f'animation-delay:{i * stagger:.2f}s">{inner}</g>'
      for i, inner in enumerate(inners)
    ]
    style = "<style>@keyframes svgfade{from{opacity:0}to{opacity:1}}</style>"
  out.write_text(f"{header}\n{style}\n" + "\n".join(layers) + "\n</svg>\n")
  return out


def render_svg_fragments(parts: Sequence[Any], out: str | Path) -> Path:
  """Compose ``parts`` into ONE SVG where each part is a reveal.js fragment.

  Each is a ``<g class="fragment">`` sharing one coordinate frame so they align.
  For a NATIVE reveal.js deck (export target): native reveal steps the fragments
  on spacebar and resets them on backward navigation. (marimo's run-mode reveal
  ignores in-cell fragments, so there it degrades to all-visible — use
  ``render_svg_autoplay`` for live marimo instead.)
  """
  out = Path(out)
  out.parent.mkdir(parents=True, exist_ok=True)

  header, inners = _svg_layers(parts)
  layers = []
  for i, inner in enumerate(inners):
    cls = "" if i == 0 else ' class="fragment"'
    layers.append(f"<g{cls}>{inner}</g>")
  out.write_text(f"{header}\n" + "\n".join(layers) + "\n</svg>\n")
  return out


def svg_image(path_or_markup: str | Path, *, max_width: int = 760) -> marimo.Html:
  """Inline an SVG into a marimo cell, scaled and centered for a 16:9 slide.

  Inlining (vs. ``mo.image``) scales crisply and avoids file-serving. Accepts an
  SVG file path or raw SVG markup.
  """
  import marimo as mo

  p = Path(str(path_or_markup))
  svg = p.read_text() if p.exists() else str(path_or_markup)
  svg = svg.replace("<svg ", '<svg style="width:100%;height:auto;" ', 1)
  return mo.Html(f'<div style="max-width:{max_width}px;margin:0 auto;">{svg}</div>')
