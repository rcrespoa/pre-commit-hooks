from __future__ import annotations

import argparse
from typing import Sequence

from pytest import main as pytest_main  # noqa: PT013


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Filenames pre-commit believes are changed.",
    )
    parser.add_argument("--src_path", help="Source path. Used to check coverage.", default=None)
    parser.add_argument("--test_paths", nargs="+", help="Comma separated test paths.", default=None)
    parser.add_argument("--min_coverage", help="Minimum test coverage", default=50, type=int)
    args = parser.parse_args(argv)

    src_path = "." if args.src_path is None else args.src_path
    test_paths = ["."] if args.test_paths is None else args.test_paths
    print(args)

    cli_args = [
        "--cov",
        src_path,
        "--cov-report",
        "term-missing",
        "--disable-pytest-warnings",
        "-v",
        "--cov-fail-under",
        str(args.min_coverage),
        *test_paths,
    ]

    return pytest_main(cli_args)


if __name__ == "__main__":
    raise SystemExit(main())
