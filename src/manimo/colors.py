"""Chart color palettes: a ``Palette`` dataclass + Paul Tol's colorblind-safe sets.

``Palette`` is the typed interface for a categorical chart scale (used by
``altair_theme(palette=...)``). Use a Paul Tol set via ``tol.<name>`` (e.g.
``tol.bright``, ``tol.muted``) or build your own with
``Palette(["#003262", "#fdb515"])``. The qualitative sets are vendored, so importing
manimo stays cheap; ``tol_colormap`` (continuous) uses the ``tol-colors`` package
lazily. A test (``test_vendored_palettes_match_tol_colors``) asserts the vendored hex
match ``tol_colors.colorsets`` so the two can't silently drift.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

# The Paul Tol qualitative sets, by name. Vendored as plain tuples (no matplotlib at
# import) but kept in lockstep with the ``tol-colors`` package by a test.
_TOL_SETS: dict[str, tuple[str, ...]] = {
  "bright": (
    "#4477AA",
    "#EE6677",
    "#228833",
    "#CCBB44",
    "#66CCEE",
    "#AA3377",
    "#BBBBBB",
  ),
  "vibrant": (
    "#EE7733",
    "#0077BB",
    "#33BBEE",
    "#EE3377",
    "#CC3311",
    "#009988",
    "#BBBBBB",
  ),
  "muted": (
    "#CC6677",
    "#332288",
    "#DDCC77",
    "#117733",
    "#88CCEE",
    "#882255",
    "#44AA99",
    "#999933",
    "#AA4499",
    "#DDDDDD",
  ),
  "high_contrast": ("#000000", "#004488", "#BB5566", "#DDAA33", "#FFFFFF"),
  "medium_contrast": (
    "#FFFFFF",
    "#6699CC",
    "#004488",
    "#EECC66",
    "#997700",
    "#EE99AA",
    "#994455",
    "#000000",
  ),
  "pale": ("#BBCCEE", "#FFCCCC", "#CCDDAA", "#EEEEBB", "#CCEEFF", "#DDDDDD"),
  "dark": ("#222255", "#663333", "#225522", "#666633", "#225555", "#555555"),
  "light": (
    "#77AADD",
    "#EE8866",
    "#EEDD88",
    "#FFAABB",
    "#99DDFF",
    "#44BB99",
    "#BBCC33",
    "#AAAA00",
    "#DDDDDD",
  ),
}


@dataclass(frozen=True)
class Palette:
  """A typed, ordered set of colors for a categorical chart scale.

  Iterable and indexable, so it drops into ``altair_theme(palette=...)``, into any
  ``alt.Scale(range=list(palette))``, and ``palette[i]`` picks one color (handy for a
  Manim diagram mark, to match the chart series).
  """

  colors: Sequence[str]

  def __iter__(self):
    """Iterate over the colors (so ``list(palette)`` yields the hex strings)."""
    return iter(self.colors)

  def __getitem__(self, i):
    """Index a single color (e.g. ``palette[0]`` for a diagram mark)."""
    return self.colors[i]

  def __len__(self):
    """Number of colors in the palette."""
    return len(self.colors)


class _TolPalettes:
  """Paul Tol's colorblind-safe qualitative palettes (https://personal.sron.nl/~pault/).

  Each attribute (``tol.bright``, ``tol.muted``, ...) is a ``Palette``.
  """

  bright = Palette(_TOL_SETS["bright"])
  vibrant = Palette(_TOL_SETS["vibrant"])
  muted = Palette(_TOL_SETS["muted"])
  high_contrast = Palette(_TOL_SETS["high_contrast"])
  medium_contrast = Palette(_TOL_SETS["medium_contrast"])
  pale = Palette(_TOL_SETS["pale"])
  dark = Palette(_TOL_SETS["dark"])
  light = Palette(_TOL_SETS["light"])


tol = _TolPalettes()


def tol_colormap(name: str = "sunset", n: int = 9) -> list[str]:
  """A Paul Tol SEQUENTIAL/DIVERGING colormap sampled to ``n`` hex colors.

  For a continuous color scale, e.g.
  ``alt.Color("v:Q", scale=alt.Scale(range=tol_colormap("YlOrBr")))``. Names:
  ``sunset``, ``nightfall``, ``BuRd``, ``PRGn``, ``YlOrBr``, ``WhOrBr``,
  ``iridescent``, ``incandescent``, the ``rainbow_*`` family (and ``_r`` reversed
  variants). ``n`` must be >= 1. Uses the ``tol-colors`` package (imported lazily).
  """
  if n < 1:
    raise ValueError(f"n must be >= 1, got {n}")
  import tol_colors
  from matplotlib.colors import to_hex

  cmap = tol_colors.colormaps[name]
  if n == 1:
    return [to_hex(cmap(0.0))]
  return [to_hex(cmap(i / (n - 1))) for i in range(n)]
