"""Command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path

from photoqa.backends import backend_status
from photoqa.workflow import analyze_photos, export_report, ingest_directory, init_database, schema_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="photoqa")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-db", help="Create or migrate the SQLite database")
    init_parser.add_argument("--db", required=True, type=Path)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a folder of photos")
    ingest_parser.add_argument("--db", required=True, type=Path)
    ingest_parser.add_argument("--photos-dir", required=True, type=Path)
    ingest_parser.add_argument("--consent-source", required=True)
    ingest_parser.add_argument(
        "--subject-id-mode",
        choices=["stem", "parent", "relative"],
        default="stem",
        help="How to derive subject_id when no manifest exists",
    )
    ingest_parser.add_argument(
        "--allow-remote-vlm",
        action="store_true",
        help="Mark consent as allowing remote VLM review for this ingest batch",
    )

    analyze_parser = subparsers.add_parser("analyze", help="Run local basic analysis")
    analyze_parser.add_argument("--db", required=True, type=Path)
    analyze_parser.add_argument("--limit", type=int)
    analyze_parser.add_argument("--force", action="store_true")

    report_parser = subparsers.add_parser("export-report", help="Export report CSV")
    report_parser.add_argument("--db", required=True, type=Path)
    report_parser.add_argument("--out", required=True, type=Path)
    report_parser.add_argument("--limit", type=int)

    schema_parser = subparsers.add_parser("schema", help="Print database tables")
    schema_parser.add_argument("--db", required=True, type=Path)

    subparsers.add_parser("backends", help="Print optional backend availability")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-db":
        init_database(args.db)
        print(f"initialized {args.db}")
        return 0

    if args.command == "ingest":
        result = ingest_directory(
            args.db,
            args.photos_dir,
            args.consent_source,
            args.subject_id_mode,
            args.allow_remote_vlm,
        )
        print(result)
        return 0

    if args.command == "analyze":
        result = analyze_photos(args.db, args.limit, args.force)
        print(result)
        return 0

    if args.command == "export-report":
        count = export_report(args.db, args.out, args.limit)
        print(f"exported {count} rows to {args.out}")
        return 0

    if args.command == "schema":
        print(schema_summary(args.db))
        return 0

    if args.command == "backends":
        print(backend_status())
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
