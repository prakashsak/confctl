"""CLI sub-command: confctl audit — view and record audit log entries."""

from __future__ import annotations

import argparse
import os
import sys

from confctl.auditor import (
    AuditError,
    append_audit_log,
    load_audit_log,
    record_entry,
    summarize_audit_log,
)

DEFAULT_LOG = os.environ.get("CONFCTL_AUDIT_LOG", "confctl_audit.log")


def build_parser(subparsers: argparse.Action | None = None) -> argparse.ArgumentParser:
    kwargs = dict(
        description="Record or display config audit log entries."
    )
    if subparsers is None:
        parser = argparse.ArgumentParser(prog="confctl audit", **kwargs)
    else:
        parser = subparsers.add_parser("audit", **kwargs)

    sub = parser.add_subparsers(dest="audit_cmd")

    # --- record sub-command ---
    rec = sub.add_parser("record", help="Append a new audit entry to the log.")
    rec.add_argument("action", help="Action label (e.g. deploy, merge, validate).")
    rec.add_argument("files", nargs="+", help="Config files involved.")
    rec.add_argument("--user", default=None, help="User performing the action.")
    rec.add_argument("--note", default=None, help="Optional free-text note.")
    rec.add_argument("--log", default=DEFAULT_LOG, help="Path to audit log file.")

    # --- show sub-command ---
    show = sub.add_parser("show", help="Display entries from the audit log.")
    show.add_argument("--log", default=DEFAULT_LOG, help="Path to audit log file.")

    return parser


def run(args: argparse.Namespace) -> int:
    try:
        if args.audit_cmd == "record":
            entry = record_entry(
                action=args.action,
                files=args.files,
                user=getattr(args, "user", None),
                note=getattr(args, "note", None),
            )
            append_audit_log(args.log, entry)
            print(f"Audit entry recorded to '{args.log}'.")

        elif args.audit_cmd == "show":
            entries = load_audit_log(args.log)
            print(summarize_audit_log(entries))

        else:
            print("Specify a sub-command: record | show", file=sys.stderr)
            return 1

    except AuditError as exc:
        print(f"audit error: {exc}", file=sys.stderr)
        return 1

    return 0
