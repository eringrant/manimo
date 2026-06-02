# Changelog

## 0.1.2

A colorblind-safe color model for charts and diagrams, with a typed palette interface.

- New `Palette(colors)` dataclass and `tol` namespace (`tol.bright`, `tol.muted`,
  `tol.high_contrast`, ...) of Paul Tol's colorblind-safe sets — a typed palette
  interface for `altair_theme(palette=...)` (no magic scheme-name strings; a bare
  string now raises with guidance). The qualitative sets are vendored (so `import
  manimo` stays cheap), and a test asserts they match the `tol-colors` package.
- **`altair_theme` color model** (breaking): signature is now
  `(*, font=None, palette=tol.bright, color=None, fontsize=None)` — the `brand`
  parameter is renamed to **`color`**. All chart colors now come from the Tol palette:
  `palette` defaults to the colorblind-safe `tol.bright`, and the single-series mark
  `color` defaults to the palette's first color. Brand colors are reserved for deck
  accents (headings/links), not chart data.
- New `tol_colormap(name, n)` — Paul Tol sequential/diverging colormaps sampled to a
  hex list, for a continuous color scale (via the `tol-colors` dependency, lazily
  imported). Validates `n >= 1`.
- An empty palette now opts out of both the category range and the default mark.

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
