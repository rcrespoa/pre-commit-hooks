from __future__ import annotations

import argparse
import os
import sys
from enum import Enum
from io import StringIO
from typing import Any
from typing import Dict
from typing import List
from typing import Sequence

from piptools.scripts.compile import cli as compile_cli


class RequirementFile(Enum):
    BASE = ["requirements.in", "requirements.txt"]
    LOCK = ["requirements-lock.txt"]


FTOE = {}
for _, req_file_enum in RequirementFile.__members__.items():
    for file_name in req_file_enum.value:
        FTOE[file_name] = req_file_enum


class CaptureSTDERR(List[str]):
    def __enter__(self) -> CaptureSTDERR:
        self._stderr = sys.stderr
        sys.stderr = self._stringio = StringIO()
        return self

    def __exit__(self, *args: list[Any]) -> None:
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stderr = self._stderr


RequirementsPairsType = Dict[str, Dict[RequirementFile, str]]


def parse_requirement_pairs(reqs_files: list[str]) -> RequirementsPairsType:
    """
    Parse the requirement files and return a dict of pairs of requirement files.

    Args:
        reqs_files (List[str]): List of requirement files

    Returns:
        RequirementsPairsType: Dict of pairs of requirement files
    """
    pairs: RequirementsPairsType = {}
    for req_file in reqs_files:
        basename = os.path.basename(req_file)
        dirname = os.path.dirname(req_file)
        key = FTOE.get(basename)
        if key is None:
            raise ValueError(f"Unknown requirement file: {req_file}")

        if dirname not in pairs:
            pairs[dirname] = {}

        pairs[dirname][key] = req_file

    return pairs


def add_requirement_pair_not_in_commit(pairs: RequirementsPairsType) -> None:
    """
    If the missing pairs exist on disk, add to the pairs dict in place.

    Args:
        pairs (RequirementsPairsType): Dict of pairs of requirement files

    Returns:
        None
    """
    for dirname, reqs in pairs.items():
        if len(reqs) == 2:
            continue

        missing_req = RequirementFile.BASE if RequirementFile.BASE not in reqs else RequirementFile.LOCK

        for missing_req_fn in missing_req.value:
            missing_req_path = os.path.join(dirname, missing_req_fn)
            if os.path.exists(missing_req_path):
                reqs[missing_req] = missing_req_path
                break


def raise_error_if_requirement_pair_missing(pairs: RequirementsPairsType) -> None:
    """
    Raise error if pair was not found.

    Args:
        pairs (RequirementsPairsType): Dict of pairs of requirement files

    Returns:
        None
    """
    for dirname, reqs in pairs.items():
        if len(reqs) != 2:
            missing_req = RequirementFile.BASE if RequirementFile.BASE not in reqs else RequirementFile.LOCK
            raise ValueError(f"Missing {missing_req} for {dirname}")


def run_check_only(reqs_files: list[str], generate_hashes: bool) -> None:
    """
    Run check only.

    Args:
        reqs_files (List[str]): List of requirement files

    Returns:
        None
    """
    pairs = parse_requirement_pairs(reqs_files)
    add_requirement_pair_not_in_commit(pairs)
    raise_error_if_requirement_pair_missing(pairs)

    # Check if the lock requirement file is up to date with the base file
    for reqs in pairs.values():
        base_req = reqs[RequirementFile.BASE]
        lock_req = reqs[RequirementFile.LOCK]

        cli_args = ["--dry-run", "-o", lock_req]

        if generate_hashes:
            cli_args.append("--generate-hashes")

        with CaptureSTDERR() as output:
            compile_cli([*cli_args, base_req], standalone_mode=False)
            pip_compile_res = output
        pip_compile_res.pop(-1)  # drop last line introduced by --dry-run

        # read lock file
        with open(lock_req) as f:
            lock_file_content = f.read().splitlines()

        if lock_file_content != pip_compile_res:
            print(lock_file_content, "\n\n---\n")
            print(pip_compile_res)
            raise ValueError(f"{lock_req} is not up to date with {base_req}")


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
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Enforce all files are checked, not just staged files.",
    )
    args = parser.parse_args(argv)

    if args.check_only:
        run_check_only(args.filenames, args.generate_hashes)
        return 0

    for req_file in [req_file for req_file in args.filenames if os.path.basename(req_file) in RequirementFile.BASE.value]:
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
