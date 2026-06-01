# Changelog

## 0.1.1

Switch chart rendering from Plotly to **Altair / Vega-Lite**.

- `figure_html` (Plotly) → `chart_html` (Altair). It delegates to Altair's own
  `Chart.to_html`, so the vega libraries it loads from CDN always match the chart's
  Vega-Lite spec version.
- New `altair_theme(*, font=None, brand=None, palette=None, fontsize=None)`: enable
  an Altair theme once so every chart inherits the deck's font, font size, single-
  series mark color, and categorical palette — no per-chart config (applies live and
  on export). `fontsize` bumps the small Vega defaults to slide-readable sizes.
- Core dependency `plotly` → `altair`; the scaffolded starter uses `mo.ui.altair_chart`.
- `build_deck` no longer injects a vega CDN (chart fragments carry their own,
  version-matched).

## 0.1.0

Initial release: turn marimo notebooks into reveal.js slide decks with Manim (SVG)
build-up diagrams (`render_svg_fragments` / `render_svg_autoplay`), a deck packager
(`build_deck`), a bundled 16:9 theme, and a `python -m manimo init` scaffolder.
