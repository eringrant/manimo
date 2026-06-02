"""Tests for the slide helpers: the optional-manim contract + pure assembly.

The render-from-Manim helpers need the optional ``anim`` group (manim + system
cairo/pango), so they aren't exercised here. What we lock down is (1) the package
imports with manim ABSENT, and (2) the pure-Python asset/packaging paths that only
need altair.
"""

import builtins
import importlib
import json
import sys

import pytest


def test_anim_imports_without_manim(monkeypatch):
  """manimo.anim imports even when manim is unavailable (lazy imports)."""
  real_import = builtins.__import__

  def _blocked(name, *args, **kwargs):
    if name == "manim" or name.startswith("manim") or name == "manim_mobject_svg":
      raise ImportError(f"blocked: {name}")
    return real_import(name, *args, **kwargs)

  for mod in ("manimo.anim", "manimo.reveal"):
    monkeypatch.delitem(sys.modules, mod, raising=False)
  monkeypatch.setattr(builtins, "__import__", _blocked)

  anim = importlib.import_module("manimo.anim")
  assert hasattr(anim, "render_svg_fragments")
  assert hasattr(anim, "svg_image")


def test_chart_html_writes_vega_fragment(tmp_path):
  """chart_html writes a self-contained vega-embed fragment via altair's to_html."""
  import altair as alt

  from manimo import chart_html

  data = alt.Data(values=[{"x": 1, "y": 1}, {"x": 2, "y": 4}, {"x": 3, "y": 9}])
  chart = alt.Chart(data).mark_line().encode(x="x:Q", y="y:Q")
  frag = chart_html(chart, tmp_path / "chart.html", width=600, height=300).read_text()
  assert "vegaEmbed" in frag
  assert "reveal-vega" in frag  # the centering wrapper
  assert "vega@" in frag  # version-matched CDN, emitted by altair's to_html
  assert "600" in frag and "300" in frag  # the fixed size reached the inlined spec


def test_altair_theme_registers_enabled_theme():
  """altair_theme enables a theme; charts then carry the font/color in to_dict."""
  import altair as alt

  from manimo import altair_theme

  try:
    cfg = altair_theme(
      font="Georgia",
      palette=["#003262", "#fdb515"],
      color="#222222",
      fontsize=15,
      name="t-test",
    )
    assert cfg["font"] == "Georgia"
    assert cfg["mark"] == {"color": "#222222"}
    assert cfg["range"] == {"category": ["#003262", "#fdb515"]}
    assert cfg["axis"]["labelFontSize"] == 15
    assert cfg["legend"]["titleFontSize"] == 15
    assert cfg["title"]["fontSize"] == round(15 * 1.25)
    chart = (
      alt.Chart(alt.Data(values=[{"x": 1, "y": 1}]))
      .mark_point()
      .encode(x="x:Q", y="y:Q")
    )
    spec = chart.to_dict()
    assert spec["config"]["font"] == "Georgia"
    assert spec["config"]["mark"]["color"] == "#222222"
    assert spec["config"]["range"]["category"] == ["#003262", "#fdb515"]
    assert spec["config"]["axis"]["labelFontSize"] == 15
  finally:
    alt.theme.enable("default")  # don't leak the enabled theme to other tests


def test_altair_theme_color_defaults_to_first_palette_color():
  """With no explicit color, the single-series mark is the palette's first color."""
  import altair as alt

  from manimo import altair_theme
  from manimo import tol

  try:
    cfg = altair_theme(palette=tol.muted, name="t-color")
    assert cfg["mark"] == {"color": tol.muted[0]}
  finally:
    alt.theme.enable("default")


def test_altair_theme_empty_palette_sets_no_range_or_mark():
  """An empty palette opts out of both the category range and the default mark."""
  import altair as alt

  from manimo import Palette
  from manimo import altair_theme

  try:
    cfg = altair_theme(palette=Palette([]), name="t-empty")
    assert "range" not in cfg
    assert "mark" not in cfg
  finally:
    alt.theme.enable("default")


def test_vendored_palettes_match_tol_colors():
  """The vendored Tol hex stay in lockstep with the tol-colors package (no drift)."""
  import tol_colors

  from manimo import tol
  from manimo.colors import _TOL_SETS

  for name, colors in _TOL_SETS.items():
    expected = tuple(str(c) for c in tol_colors.colorsets[name])
    assert colors == expected, f"vendored {name!r} drifted from tol_colors"
    assert tuple(getattr(tol, name).colors) == expected


def test_tol_colormap_rejects_nonpositive_n():
  """tol_colormap validates n >= 1 instead of silently returning one color."""
  import pytest

  from manimo import tol_colormap

  with pytest.raises(ValueError, match="n must be"):
    tol_colormap("sunset", n=0)


def test_tol_palette_dataclass_and_colormap():
  """tol.<name> is an iterable Palette; tol_colormap returns chart-ready hex."""
  from manimo import Palette
  from manimo import tol
  from manimo import tol_colormap

  assert isinstance(tol.bright, Palette)
  assert len(tol.bright) >= 5
  assert all(c.startswith("#") for c in tol.bright)
  assert list(tol.muted) == list(tol.muted.colors)  # iterable
  assert tol.muted[0] == tol.muted.colors[0]  # indexable (for diagram marks)

  cmap = tol_colormap("sunset", n=5)
  assert len(cmap) == 5
  assert all(c.startswith("#") for c in cmap)


def test_altair_theme_defaults_to_tol_bright():
  """With no palette, charts get the colorblind-safe Tol 'bright' set."""
  import altair as alt

  from manimo import altair_theme
  from manimo import tol

  try:
    cfg = altair_theme(name="t-default")
    assert cfg["range"]["category"] == list(tol.bright.colors)
  finally:
    alt.theme.enable("default")


def test_altair_theme_accepts_palette_dataclass():
  """altair_theme(palette=tol.muted) uses the Palette's colors."""
  import altair as alt

  from manimo import altair_theme
  from manimo import tol

  try:
    cfg = altair_theme(palette=tol.muted, name="t-muted")
    assert cfg["range"]["category"] == list(tol.muted.colors)
  finally:
    alt.theme.enable("default")


def test_altair_theme_rejects_string_palette():
  """A bare string is no longer accepted — the error points to tol.<name>."""
  import pytest

  from manimo import altair_theme

  with pytest.raises(TypeError, match="manimo.tol"):
    altair_theme(palette="muted", name="t-str")


def test_build_deck_assembles_sections(tmp_path):
  """build_deck wires section assets into a reveal.js HTML shell."""
  from manimo.reveal import build_deck

  asset = tmp_path / "a.svg"
  asset.write_text("<svg><g></g></svg>")
  out = build_deck(
    [{"title": "Mechanism", "asset": asset}],
    tmp_path / "deck.html",
    title="My deck",
  )
  html = out.read_text()
  assert "reveal" in html.lower()
  assert "Mechanism" in html


def test_copy_theme_copies_bundled_files(tmp_path):
  """_copy_theme drops the two theme files and is idempotent without overwrite."""
  from manimo.scaffold import _copy_theme

  written = _copy_theme(tmp_path)
  assert {p.name for p in written} == {"_slide_theme.css", "_slide_head.html"}
  assert (tmp_path / "_slide_theme.css").exists()
  assert (tmp_path / "_slide_head.html").exists()
  # second call copies nothing (files already present, overwrite=False)
  assert _copy_theme(tmp_path) == []


def test_init_deck_writes_runnable_deck(tmp_path):
  """init_deck scaffolds a notebook + layout + theme and refuses to clobber."""
  from manimo import init_deck

  notebook = init_deck(tmp_path, name="mydeck")
  assert notebook == tmp_path / "mydeck.py"

  src = notebook.read_text()
  assert "marimo.App(" in src
  assert 'layout_file="layouts/mydeck.slides.json"' in src
  assert 'css_file="_slide_theme.css"' in src

  layout = json.loads((tmp_path / "layouts" / "mydeck.slides.json").read_text())
  assert layout["type"] == "slides"
  assert layout["data"]["cells"][0]["type"] == "skip"
  assert (tmp_path / "_slide_theme.css").exists()

  with pytest.raises(FileExistsError):
    init_deck(tmp_path, name="mydeck")


def test_render_svg_fragments_smoke(tmp_path):
  """render_svg_fragments emits an SVG with fragment groups (needs manim + cairo)."""
  pytest.importorskip("manim")
  pytest.importorskip("manim_mobject_svg")
  from manim import RIGHT
  from manim import Square

  from manimo import render_svg_fragments

  try:
    out = render_svg_fragments([Square(), Square().shift(RIGHT)], tmp_path / "d.svg")
  except Exception as exc:  # rendering needs system cairo/pango; skip if absent
    pytest.skip(f"manim render unavailable in this environment: {exc}")

  svg = out.read_text()
  assert "<svg" in svg
  assert 'class="fragment"' in svg  # second part is a reveal fragment


def test_render_svg_autoplay_loop_vs_oneshot(tmp_path):
  """loop=True emits infinite per-layer keyframes; loop=False a one-shot build-up."""
  pytest.importorskip("manim")
  pytest.importorskip("manim_mobject_svg")
  from manim import RIGHT
  from manim import Square

  from manimo import render_svg_autoplay

  parts = [Square(), Square().shift(RIGHT)]
  try:
    looped = render_svg_autoplay(parts, tmp_path / "loop.svg", loop=True).read_text()
    once = render_svg_autoplay(parts, tmp_path / "once.svg").read_text()
  except Exception as exc:  # rendering needs system cairo/pango; skip if absent
    pytest.skip(f"manim render unavailable in this environment: {exc}")

  assert "infinite" in looped and "svgfade0" in looped
  assert "forwards" in once and "infinite" not in once


def test_build_deck_autoplay_section_wires_restart_hook(tmp_path):
  """An autoplay section carries the class; build_deck wires the slidechanged hook."""
  from manimo import build_deck

  asset = tmp_path / "a.svg"
  asset.write_text("<svg><g></g></svg>")
  page = build_deck(
    [{"title": "Intuition", "asset": asset, "autoplay": True}],
    tmp_path / "deck.html",
  ).read_text()
  assert 'class="autoplay"' in page
  assert "slidechanged" in page


def test_build_deck_escapes_titles(tmp_path):
  """Deck and section titles are HTML-escaped."""
  from manimo import build_deck

  page = build_deck(
    [{"title": "x < y & z", "asset": "<svg/>"}],
    tmp_path / "deck.html",
    title="A & B",
  ).read_text()
  assert "x &lt; y &amp; z" in page
  assert "A &amp; B" in page


def test_build_deck_accepts_raw_markup_asset(tmp_path):
  """A long raw-markup asset is embedded, not mistaken for a path (no OSError)."""
  from manimo import build_deck

  markup = "<div>" + "x" * 5000 + "</div>"  # long enough to be an illegal filename
  page = build_deck(
    [{"title": "Raw", "asset": markup}], tmp_path / "deck.html"
  ).read_text()
  assert markup in page


def test_build_deck_embeds_chart_fragment(tmp_path):
  """A chart_html asset (carrying its own matched CDN) is embedded into the deck."""
  import altair as alt

  from manimo import build_deck
  from manimo import chart_html

  chart = (
    alt.Chart(alt.Data(values=[{"x": 1, "y": 1}])).mark_point().encode(x="x:Q", y="y:Q")
  )
  asset = chart_html(chart, tmp_path / "c.html")
  with_chart = build_deck(
    [{"title": "C", "asset": asset}], tmp_path / "d1.html"
  ).read_text()
  assert "vegaEmbed" in with_chart and "vega@" in with_chart

  no_chart = build_deck(
    [{"title": "S", "asset": "<svg/>"}], tmp_path / "d2.html"
  ).read_text()
  assert "vegaEmbed" not in no_chart  # build_deck adds no chart embed on its own
