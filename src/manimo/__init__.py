"""manimo: present marimo notebooks as reveal.js slide decks, with Manim diagrams.

The public API is organized by what you're building:

Scaffold a deck
- ``init_deck`` — write a runnable starter deck into a directory (notebook +
  layout + theme). Also ``python -m manimo init <dir>``.
- ``THEME_DIR`` — path to the bundled theme files, for wiring a deck by hand.

Diagrams (Manim -> vector SVG; shared by both targets)
- ``render_svg_autoplay`` — a build-up SVG that plays on its own (CSS).
- ``render_svg_fragments`` — a build-up SVG that steps on spacebar (native reveal).
- ``register_fonts`` — register fonts before constructing Manim ``Text``.

In a live ``marimo run`` deck
- ``svg_image`` — inline an SVG into a marimo cell so reveal.js can show it.

Charts (live and export)
- ``altair_theme`` — enable an Altair theme once so every chart inherits the deck's
  font, size, and colors (no per-chart config); applies live and on export. Charts
  default to a colorblind-safe Paul Tol palette.
- ``Palette`` / ``tol`` — a categorical-palette dataclass and Paul Tol's
  colorblind-safe sets (``tol.bright``, ``tol.muted``, ...) for ``altair_theme``.
- ``tol_colormap`` — Paul Tol sequential/diverging colormaps as hex lists (for a
  continuous color scale).

Export a standalone reveal.js deck
- ``chart_html`` — an Altair / Vega-Lite chart -> an interactive HTML asset.
- ``build_deck`` — package rendered assets into a self-contained ``deck.html``.
"""

from pathlib import Path

# Bundled slide theme assets, shipped as package data. Defined before the submodule
# imports below because scaffold.py imports it back.
THEME_DIR = Path(__file__).parent / "theme"

from .anim import register_fonts  # noqa: E402
from .anim import render_svg_autoplay  # noqa: E402
from .anim import render_svg_fragments  # noqa: E402
from .anim import svg_image  # noqa: E402
from .colors import Palette  # noqa: E402
from .colors import tol  # noqa: E402
from .colors import tol_colormap  # noqa: E402
from .reveal import altair_theme  # noqa: E402
from .reveal import build_deck  # noqa: E402
from .reveal import chart_html  # noqa: E402
from .scaffold import init_deck  # noqa: E402

__version__ = "0.1.2"

__all__ = [
  "__version__",
  # scaffold
  "init_deck",
  "THEME_DIR",
  # diagrams (Manim -> SVG)
  "render_svg_autoplay",
  "render_svg_fragments",
  "register_fonts",
  # live marimo deck
  "svg_image",
  # charts (live + export)
  "altair_theme",
  "Palette",
  "tol",
  "tol_colormap",
  # reveal.js export
  "chart_html",
  "build_deck",
]
