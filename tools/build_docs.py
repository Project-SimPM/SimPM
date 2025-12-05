from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_SOURCE = ROOT / "docs" / "source"
HTML_BUILD_DIR = ROOT / "docs" / "_build" / "html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build project documentation without relying on platform-specific tools."
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove the existing HTML build directory before rebuilding.",
    )
    return parser.parse_args()


def clean_build_dir() -> None:
    if HTML_BUILD_DIR.exists():
        shutil.rmtree(HTML_BUILD_DIR)


def main() -> int:
    args = parse_args()

    if args.clean:
        clean_build_dir()

    sys.path.insert(0, str(ROOT / "src"))
    os.environ.setdefault("PYTHONPATH", str(ROOT / "src"))

    from sphinx.cmd import build

    return build.main([
        "-b",
        "html",
        str(DOCS_SOURCE),
        str(HTML_BUILD_DIR),
    ])


if __name__ == "__main__":
    raise SystemExit(main())
