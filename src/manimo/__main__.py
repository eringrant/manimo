"""CLI for manimo: scaffold a runnable starter deck into your project.

Usage:
    python -m manimo init <dir> [--name deck]
"""

from __future__ import annotations

import argparse
import sys

from .scaffold import init_deck


def main(argv: list[str] | None = None) -> int:
  """Parse args and run the requested command."""
  parser = argparse.ArgumentParser(
    prog="python -m manimo",
    description="Scaffold a marimo reveal.js slide deck.",
  )
  sub = parser.add_subparsers(dest="command", required=True)

  init = sub.add_parser("init", help="write a runnable starter deck into a directory")
  init.add_argument("dest", help="directory to create the deck in")
  init.add_argument("--name", default="main", help="notebook name (default: main)")
  init.add_argument("--overwrite", action="store_true", help="replace existing files")

  args = parser.parse_args(argv)
  if args.command == "init":
    try:
      notebook = init_deck(args.dest, name=args.name, overwrite=args.overwrite)
    except FileExistsError as exc:
      print(f"error: {exc} (use --overwrite to replace)", file=sys.stderr)
      return 1
    deck_dir = notebook.parent
    files = [
      notebook.name,
      f"layouts/{args.name}.slides.json",
      "_slide_theme.css",
      "_slide_head.html",
    ]
    print(f"Created deck in {deck_dir}/")
    for f in files:
      print(f"  {f}")
    print(f"\nPresent it:  uv run marimo run {notebook}")
    print(f"Edit it:     uv run marimo edit {notebook}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
