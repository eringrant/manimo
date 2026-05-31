"""Render a deck's visual ASSETS as reveal.js-ready files.

The idea: render just the *assets* (charts and diagrams) into reveal-native files
you drop into a reveal.js deck, rather than exporting whole slides.

- ``figure_html``  — a Plotly figure → a self-contained, interactive HTML fragment
  (plotly.js from CDN). No Chrome / kaleido needed; renders crisp + interactive in
  reveal. This is the recommended chart asset.
- ``render_svg_fragments`` / ``render_svg_autoplay`` — Manim graphics → SVG
  (re-exported from ``.anim``). ``render_svg_fragments`` is the one that steps
  natively on spacebar in reveal.js.
- ``svg_image`` — inline an SVG (re-exported from ``.anim``).

Typical use: a chart/diagram cell displays in marimo AND writes its reveal asset,
e.g. ``figure_html(fig, Path(__file__).parent / "reveal-assets" / "result.html")``.
Collect the files in ``reveal-assets/`` and embed them in a reveal ``<section>``.
"""

from __future__ import annotations

import html
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .anim import register_fonts  # re-export so reveal assets are one import
from .anim import render_svg_autoplay  # re-export so reveal assets are one import
from .anim import render_svg_fragments  # re-export so reveal assets are one import
from .anim import svg_image  # re-export so reveal assets are one import

__all__ = [
  "figure_html",
  "build_deck",
  "register_fonts",
  "render_svg_fragments",
  "render_svg_autoplay",
  "svg_image",
]


REVEAL_CDN = "https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist"


def figure_html(
  fig: Any,
  out: str | Path,
  *,
  embeddable: bool = True,
  include_plotlyjs: str = "cdn",
  div_class: str = "reveal-plot",
  font: str | None = None,
) -> Path:
  """Write a Plotly ``fig`` as an interactive HTML asset for reveal.js.

  With ``embeddable=True`` (default) writes a fragment — a ``<div>`` + the plotly
  script (plotly.js pulled from CDN) — which you can drop straight into a reveal
  ``<section>``; it also renders on its own if opened directly. ``embeddable=False``
  writes a full standalone HTML page. The figure autosizes to its container, so
  set the figure's ``height`` and let width be 100%. Pass ``font`` to set the
  chart's typeface (must also be loaded by the page); leave it ``None`` to use the
  figure's default. The template imposes no specific font — supply your brand font.
  """
  out = Path(out)
  out.parent.mkdir(parents=True, exist_ok=True)
  if font:
    fig.update_layout(font=dict(family=f"{font}, system-ui, sans-serif"))
  html = fig.to_html(
    include_plotlyjs=include_plotlyjs,
    full_html=not embeddable,
    default_width="100%",
    default_height="100%",
  )
  if embeddable:
    html = f'<div class="{div_class}" style="width:100%;height:100%;">{html}</div>'
  out.write_text(html)
  return out


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
  CSS-autoplay SVGs (mark those sections ``"autoplay": True``). Pass your brand
  color/font and a ``google_fonts`` stylesheet URL to load it; defaults to a
  neutral system stack. SVGs with ``<g class="fragment">`` step natively on
  spacebar; Plotly fragments render interactively.
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
  .reveal .reveal-plot {{ width: 100%; }}
</style></head><body>
<div class="reveal"><div class="slides">
{"".join(secs)}
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
