import sys
import pathlib
import pytest


if __name__ == "__main__":
    root = pathlib.Path(__file__).parent

    # Adjust "tests" if your test folder name is different
    args = [str(root / "tests")]

    # Optional: add flags here, e.g. "-q" or "-vv"
    # args.append("-vv")

    exit_code = pytest.main(args)
    sys.exit(exit_code)
