from __future__ import annotations

import argparse
import os
from enum import Enum
from typing import Sequence

from piptools.scripts.compile import cli as compile_cli


class RequirementFile(Enum):
    BASE = ["requirements.in", "requirements.txt"]
    LOCK = ["requirements-lock.txt"]


FTOE = {}
for _, req_file_enum in RequirementFile.__members__.items():
    for file_name in req_file_enum.value:
        FTOE[file_name] = req_file_enum


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Filenames pre-commit believes are changed.",
    )
    parser.add_argument(
        "--generate-hashes",
        action="store_true",
        help="Enforce all files are checked, not just staged files.",
    )
    args = parser.parse_args(argv)

    reqs_files = args.filenames
    base_req_files = [req_file for req_file in reqs_files if os.path.basename(req_file) in RequirementFile.BASE.value]

    for req_file in base_req_files:
        dirname = os.path.dirname(req_file)

        cli_args = [
            "-o",
            os.path.join(dirname, RequirementFile.LOCK.value[0]),
        ]

        if args.generate_hashes:
            cli_args.append("--generate-hashes")

        try:
            compile_cli([*cli_args, req_file], standalone_mode=False)
        except SystemExit as e:
            return e.code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
