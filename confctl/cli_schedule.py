"""CLI sub-command: confctl schedule."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from confctl.scheduler import (
    ScheduleError,
    create_job,
    list_pending,
    load_schedule,
    mark_done,
    save_schedule,
)

_DEFAULT_SCHEDULE = ".confctl_schedule.json"


def build_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = parent.add_parser("schedule", help="manage deferred config operations")
    sub = p.add_subparsers(dest="schedule_cmd", required=True)

    add_p = sub.add_parser("add", help="add a new job")
    add_p.add_argument("action", help="action name (e.g. merge, validate)")
    add_p.add_argument("files", nargs="+", help="config files involved")
    add_p.add_argument("--run-at", required=True, help="ISO-8601 datetime")
    add_p.add_argument("--note", default="", help="optional note")
    add_p.add_argument(
        "--schedule-file", default=_DEFAULT_SCHEDULE, help="path to schedule JSON"
    )

    list_p = sub.add_parser("list", help="list pending jobs")
    list_p.add_argument(
        "--schedule-file", default=_DEFAULT_SCHEDULE, help="path to schedule JSON"
    )
    list_p.add_argument("--all", dest="show_all", action="store_true")

    done_p = sub.add_parser("done", help="mark a job as done")
    done_p.add_argument("index", type=int, help="job index (0-based)")
    done_p.add_argument(
        "--schedule-file", default=_DEFAULT_SCHEDULE, help="path to schedule JSON"
    )

    return p


def run(args: argparse.Namespace) -> int:
    schedule_file = Path(args.schedule_file)
    try:
        if args.schedule_cmd == "add":
            jobs = load_schedule(schedule_file)
            job = create_job(args.action, args.files, args.run_at, note=args.note)
            jobs.append(job)
            save_schedule(jobs, schedule_file)
            print(f"Scheduled job #{len(jobs) - 1}: {args.action} at {args.run_at}")

        elif args.schedule_cmd == "list":
            jobs = load_schedule(schedule_file)
            display = jobs if args.show_all else list_pending(jobs)
            if not display:
                print("No jobs found.")
            else:
                print(json.dumps(display, indent=2))

        elif args.schedule_cmd == "done":
            jobs = load_schedule(schedule_file)
            jobs = mark_done(jobs, args.index)
            save_schedule(jobs, schedule_file)
            print(f"Job #{args.index} marked as done.")

    except ScheduleError as exc:
        print(f"schedule error: {exc}", file=sys.stderr)
        return 1
    return 0
