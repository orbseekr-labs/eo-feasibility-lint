"""Command line interface.

Exit codes (spec section 41):

* 0 - result below the configured fail threshold
* 1 - configured feasibility threshold reached
* 2 - invalid input or CLI usage
* 3 - internal tool failure

An internal bug must never masquerade as a feasibility finding.
"""

from __future__ import annotations

import argparse
import sys

from . import render
from .aggregate import MissionSelectionError, build_report
from .catalog import CatalogError, load_catalog
from .loader import RequirementError, load_requirement
from .models import CONDITIONAL, FAIL, RULESET_VERSION, SEVERITY, UNKNOWN

EXIT_OK = 0
EXIT_THRESHOLD_REACHED = 1
EXIT_USAGE = 2
EXIT_INTERNAL = 3

FAIL_ON_THRESHOLDS = {"fail": FAIL, "unknown": UNKNOWN, "conditional": CONDITIONAL}

PROGRAM = "eo-feasibility-lint"
DESCRIPTION = (
    "Deterministic, offline linter that checks explicit Earth observation "
    "requirements against a static satellite mission capability catalog."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM, description=DESCRIPTION)
    parser.add_argument(
        "--version",
        action="version",
        version=f"{PROGRAM} {RULESET_VERSION}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser(
        "check", help="check a requirement file against the mission catalog"
    )
    check.add_argument("file", metavar="FILE", help="requirement file (.yaml, .yml or .json)")
    check.add_argument(
        "--mission",
        action="append",
        default=[],
        metavar="MISSION_ID",
        help="evaluate this mission; repeatable; overrides candidate_missions",
    )
    check.add_argument("--format", choices=("text", "json"), default="text")
    check.add_argument(
        "--fail-on",
        choices=tuple(FAIL_ON_THRESHOLDS),
        default="fail",
        help="portfolio verdict severity that exits 1 (default: fail)",
    )

    subparsers.add_parser("list-missions", help="list supported mission profiles")

    show = subparsers.add_parser("show-mission", help="show one mission's catalog entry")
    show.add_argument("mission_id", metavar="MISSION_ID")

    subparsers.add_parser("rules", help="list reason codes and their effects")

    return parser


def _check(args, stdout, stderr) -> int:
    catalog = load_catalog()

    try:
        requirement = load_requirement(args.file, catalog.mission_ids())
    except RequirementError as error:
        print(f"{PROGRAM}: {error}", file=stderr)
        return EXIT_USAGE

    try:
        report = build_report(requirement, catalog, tuple(args.mission))
    except MissionSelectionError as error:
        print(f"{PROGRAM}: {error}", file=stderr)
        return EXIT_USAGE

    rendered = render.render_json(report) if args.format == "json" else render.render_text(report)
    print(rendered, end="" if rendered.endswith("\n") else "\n", file=stdout)

    threshold = FAIL_ON_THRESHOLDS[args.fail_on]
    if SEVERITY[report.portfolio_verdict] >= SEVERITY[threshold]:
        return EXIT_THRESHOLD_REACHED
    return EXIT_OK


def _show_mission(args, stdout, stderr) -> int:
    catalog = load_catalog()
    mission = catalog.get(args.mission_id)
    if mission is None:
        print(
            f"{PROGRAM}: unknown mission id: {args.mission_id}; supported: "
            + ", ".join(catalog.mission_ids()),
            file=stderr,
        )
        return EXIT_USAGE
    print(render.render_mission(catalog, mission), end="", file=stdout)
    return EXIT_OK


def main(argv: list[str] | None = None, stdout=None, stderr=None) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    args = build_parser().parse_args(argv)

    try:
        if args.command == "check":
            return _check(args, stdout, stderr)
        if args.command == "list-missions":
            print(render.render_mission_list(load_catalog()), end="", file=stdout)
            return EXIT_OK
        if args.command == "show-mission":
            return _show_mission(args, stdout, stderr)
        if args.command == "rules":
            print(render.render_rules(), end="", file=stdout)
            return EXIT_OK
    except CatalogError as error:
        print(f"{PROGRAM}: internal failure: {error}", file=stderr)
        return EXIT_INTERNAL
    except Exception as error:
        print(f"{PROGRAM}: internal failure: {type(error).__name__}: {error}", file=stderr)
        return EXIT_INTERNAL

    print(f"{PROGRAM}: unknown command: {args.command}", file=stderr)
    return EXIT_USAGE


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
