"""CLI sub-command: snapshot — capture and diff config snapshots."""

import argparse
import json
import sys

from confctl.snapshotter import (
    SnapshotError,
    capture_snapshot,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


def build_parser(subparsers: argparse.Action) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "snapshot",
        help="Capture or diff config snapshots",
    )
    sub = parser.add_subparsers(dest="snapshot_cmd", required=True)

    # capture sub-command
    capture_p = sub.add_parser("capture", help="Capture a new snapshot")
    capture_p.add_argument("configs", nargs="+", metavar="FILE", help="Config files to snapshot")
    capture_p.add_argument("-o", "--output", required=True, metavar="SNAPSHOT", help="Output snapshot file")

    # diff sub-command
    diff_p = sub.add_parser("diff", help="Diff two snapshots")
    diff_p.add_argument("old", metavar="OLD_SNAPSHOT", help="Older snapshot file")
    diff_p.add_argument("new", metavar="NEW_SNAPSHOT", help="Newer snapshot file")
    diff_p.add_argument("--json", dest="as_json", action="store_true", help="Output diff as JSON")

    return parser


def run(args: argparse.Namespace) -> int:
    try:
        if args.snapshot_cmd == "capture":
            snapshot = capture_snapshot(args.configs)
            save_snapshot(snapshot, args.output)
            print(f"Snapshot saved to {args.output} ({len(args.configs)} file(s))")

        elif args.snapshot_cmd == "diff":
            old = load_snapshot(args.old)
            new = load_snapshot(args.new)
            diff = diff_snapshots(old, new)
            if args.as_json:
                print(json.dumps(diff, indent=2, default=str))
            else:
                for path, info in diff.items():
                    status = info["status"]
                    print(f"[{status.upper()}] {path}")
                    if status == "changed":
                        for k, v in info.get("added", {}).items():
                            print(f"  + {k}: {v}")
                        for k, v in info.get("removed", {}).items():
                            print(f"  - {k}: {v}")
                        for k, v in info.get("changed", {}).items():
                            print(f"  ~ {k}: {v['old']!r} -> {v['new']!r}")
    except SnapshotError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
