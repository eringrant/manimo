"""Tests for the slide helpers: the optional-manim contract + pure assembly.

The render-from-Manim helpers need the optional ``anim`` group (manim + system
cairo/pango), so they aren't exercised here. What we lock down is (1) the package
imports with manim ABSENT, and (2) the pure-Python asset/packaging paths that only
need plotly.
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


def test_figure_html_writes_plotly_fragment(tmp_path):
  """figure_html writes a self-contained interactive Plotly HTML fragment."""
  import plotly.graph_objects as go

  from manimo.reveal import figure_html

  fig = go.Figure(go.Scatter(x=[1, 2, 3], y=[1, 4, 9]))
  out = figure_html(fig, tmp_path / "chart.html")
  html = out.read_text()
  assert out.exists()
  assert "plotly" in html.lower()


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


def test_figure_html_full_page(tmp_path):
  """embeddable=False writes a standalone HTML page."""
  import plotly.graph_objects as go

  from manimo import figure_html

  fig = go.Figure(go.Bar(x=["a"], y=[1]))
  page = figure_html(fig, tmp_path / "p.html", embeddable=False).read_text()
  assert "<html" in page.lower()
