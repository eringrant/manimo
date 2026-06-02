"""Render a deck's visual ASSETS as reveal.js-ready files.

The idea: render just the *assets* (charts and diagrams) into reveal-native files
you drop into a reveal.js deck, rather than exporting whole slides.

- ``chart_html`` — an Altair / Vega-Lite chart → a self-contained, interactive HTML
  fragment (vega libraries from CDN, wired up by ``build_deck``). No Chrome /
  kaleido needed; vector (SVG) and interactive (tooltips, pan/zoom) in reveal.
- ``render_svg_fragments`` / ``render_svg_autoplay`` — Manim graphics → SVG
  (re-exported from ``.anim``). ``render_svg_fragments`` is the one that steps
  natively on spacebar in reveal.js.
- ``svg_image`` — inline an SVG (re-exported from ``.anim``).

Typical use: a chart/diagram cell displays in marimo AND writes its reveal asset,
e.g. ``chart_html(chart, Path(__file__).parent / "reveal-assets" / "result.html")``.
Collect the files in ``reveal-assets/`` and embed them with ``build_deck``.
"""

from __future__ import annotations

import hashlib
import html
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .anim import register_fonts  # re-export so reveal assets are one import
from .anim import render_svg_autoplay  # re-export so reveal assets are one import
from .anim import render_svg_fragments  # re-export so reveal assets are one import
from .anim import svg_image  # re-export so reveal assets are one import
from .colors import Palette
from .colors import tol

__all__ = [
  "chart_html",
  "altair_theme",
  "build_deck",
  "register_fonts",
  "render_svg_fragments",
  "render_svg_autoplay",
  "svg_image",
]


REVEAL_CDN = "https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist"


def chart_html(
  chart: Any, out: str | Path, *, width: int | None = 760, height: int | None = 340
) -> Path:
  """Write an Altair chart as an interactive reveal.js fragment.

  Delegates to Altair's own ``Chart.to_html``, so the vega libraries it loads from
  CDN always match the chart's Vega-Lite spec version (hand-rolling them risks a
  schema/runtime mismatch). Vector (SVG renderer), interactive (tooltips, pan/zoom),
  self-contained — no Python kernel, Chrome, or kaleido. Font/colors come from
  ``altair_theme`` (or the chart's own config).

  ``width`` / ``height`` are applied to the chart as fixed pixels — a fixed width is
  reliable inside reveal's transformed slides, where responsive ``"container"`` width
  measures 0. Pass ``None`` to keep the chart's own size.
  """
  out = Path(out)
  out.parent.mkdir(parents=True, exist_ok=True)

  sized = {}
  if width is not None:
    sized["width"] = width
  if height is not None:
    sized["height"] = height
  if sized:
    chart = chart.properties(**sized)

  vid = hashlib.md5(json.dumps(chart.to_dict()).encode()).hexdigest()[:8]  # noqa: S324
  frag = chart.to_html(
    fullhtml=False,
    output_div=f"vega-{vid}",
    embed_options={"renderer": "svg", "actions": False},
  )
  out.write_text(f'<div class="reveal-vega">{frag}</div>\n')
  return out


def altair_theme(
  *,
  font: str | None = None,
  palette: Palette | Sequence[str] | None = tol.bright,
  color: str | None = None,
  fontsize: int | None = None,
  name: str = "manimo",
) -> dict[str, Any]:
  """Register and enable an Altair theme so every chart inherits the deck's look.

  Call once in a setup cell; charts then pick up these defaults with no per-chart
  ``.configure``:

  - ``font`` — applied to all chart text.
  - ``palette`` — the categorical color **range**, used when a chart encodes by
    ``color`` (i.e. multi-series). A ``Palette`` (e.g. ``manimo.tol.muted`` or your
    own ``Palette([...])``) or a plain list of colors. Defaults to ``tol.bright``, a
    colorblind-safe Paul Tol set; pass ``None`` for Vega's own default palette.
  - ``color`` — the mark color for a **single-series** chart. Defaults to the
    palette's first color, so single- and multi-series charts stay in the same
    colorblind-safe family. (Brand colors are for deck accents — headings, links —
    not chart data; keep them out of here.)
  - ``fontsize`` — base text size in px for axis/legend labels and titles (chart
    titles get a modest bump). Vega's defaults (~10px) read small on a projected
    slide; ~14-16 is comfortable.

  The config travels in ``chart.to_dict()``, so it applies to a live
  ``mo.ui.altair_chart`` AND to the ``chart_html`` reveal export. Returns the
  theme's config dict.
  """
  import altair as alt

  config: dict[str, Any] = {}
  if font:
    config["font"] = font
  colors: list[str] = []
  if palette is not None:
    if isinstance(palette, str):
      raise TypeError(
        f"palette should be a Palette (e.g. manimo.tol.muted) or a list of colors, "
        f"not the string {palette!r}"
      )
    colors = list(palette)
  if colors:
    config["range"] = {"category": colors}
  # Single-series mark: an explicit `color`, else the palette's first color, so a
  # lone series stays in the same family as a multi-series chart.
  mark = color if color is not None else (colors[0] if colors else None)
  if mark:
    config["mark"] = {"color": mark}
  if fontsize:
    axis = config.setdefault("axis", {})
    axis["labelFontSize"] = axis["titleFontSize"] = fontsize
    legend = config.setdefault("legend", {})
    legend["labelFontSize"] = legend["titleFontSize"] = fontsize
    config.setdefault("title", {})["fontSize"] = round(fontsize * 1.25)
  # altair types the name as LiteralString, but any str works (it's a registry key).
  alt.theme.register(name, enable=True)(lambda: {"config": config})  # ty: ignore[invalid-argument-type]
  return config


def _read_asset(asset: str | Path) -> str:
  """Return file text if ``asset`` is an existing path, else treat it as markup."""
  try:
    p = Path(asset)
    if p.exists():
      return p.read_text()
  except OSError:
    pass  # long raw markup isn't a real path (e.g. "File name too long")
  return str(asset)


def build_deck(
  sections: Sequence[dict[str, Any]],
  out: str | Path,
  *,
  title: str | None = None,
  subtitle: str | None = None,
  brand: str = "#1f6feb",
  font: str = "system-ui, sans-serif",
  google_fonts: str | None = None,
  transition: str = "none",
) -> Path:
  """Assemble a native reveal.js deck (HTML) from rendered ASSETS — a packager.

  This is a packager, not a slide renderer.
  ``sections`` is a list of dicts: ``{"title": str, "asset": <path or markup>,
  "autoplay": bool}``. ``asset`` may be a path to an ``.svg``/``.html`` asset
  (read inline) or raw markup. Prewires reveal.js (CDN), the ``brand`` heading
  color, the ``font`` family, and the ``slidechanged`` hook that restarts
  CSS-autoplay SVGs (mark those sections ``"autoplay": True``). ``chart_html``
  fragments carry their own version-matched vega libraries. Pass your brand
  color/font and a ``google_fonts`` stylesheet URL to load it; defaults to a
  neutral system stack. SVGs with ``<g class="fragment">`` step natively on
  spacebar; ``chart_html`` charts are interactive.
  """
  out = Path(out)
  out.parent.mkdir(parents=True, exist_ok=True)

  secs = []
  if title:
    sub = f"<p>{html.escape(subtitle)}</p>" if subtitle else ""
    secs.append(f"<section><h1>{html.escape(title)}</h1>{sub}</section>")
  for s in sections:
    body = _read_asset(s.get("asset", ""))
    head = f"<h2>{html.escape(s['title'])}</h2>" if s.get("title") else ""
    cls = ' class="autoplay"' if s.get("autoplay") else ""
    secs.append(f'<section{cls}>{head}<div class="asset">{body}</div></section>')

  body_html = "".join(secs)
  fonts_link = (
    f'<link rel="preconnect" href="https://fonts.googleapis.com">'
    f'<link rel="stylesheet" href="{google_fonts}">'
    if google_fonts
    else ""
  )
  page = f"""<!doctype html><html><head><meta charset="utf-8">
{fonts_link}
<link rel="stylesheet" href="{REVEAL_CDN}/reveal.css">
<link rel="stylesheet" href="{REVEAL_CDN}/theme/white.css">
<style>
  .reveal {{ font-family: {font}; }}
  .reveal h1, .reveal h2, .reveal h3 {{ font-family: {font}; color: {brand}; }}
  .reveal .asset {{ max-width: 860px; margin: 0 auto; }}
  .reveal .asset svg {{ width: 100%; height: auto; }}
  /* chart_html charts render at a fixed pixel size; keep it (don't stretch). */
  .reveal .reveal-vega {{ display: flex; justify-content: center; }}
  .reveal .reveal-vega svg {{ width: auto; height: auto; max-width: 100%; }}
</style></head><body>
<div class="reveal"><div class="slides">
{body_html}
</div></div>
<script src="{REVEAL_CDN}/reveal.js"></script>
<script>
Reveal.initialize({{ transition: "{transition}", hash: false }});
Reveal.on("slidechanged", function (e) {{
  var a = e.currentSlide.querySelector(".autoplay .asset, .asset.autoplay");
  if (a) {{ a.innerHTML = a.innerHTML; }}  /* reparse -> restart CSS autoplay */
}});
</script></body></html>"""
  out.write_text(page)
  return out
