"""CLI sub-command for rendering config templates."""

import argparse
import sys

from confctl.renderer import RenderError, render_file


def build_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Register the 'render' sub-command."""
    parser = subparsers.add_parser(
        "render",
        help="Render a config template with key=value variables.",
    )
    parser.add_argument("template", help="Path to the template file.")
    parser.add_argument(
        "--set",
        metavar="KEY=VALUE",
        dest="variables",
        action="append",
        default=[],
        help="Set a template variable (can be repeated).",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        default=None,
        help="Write rendered output to FILE instead of stdout.",
    )
    return parser


def _parse_variables(pairs: list[str]) -> dict:
    """Parse a list of 'KEY=VALUE' strings into a dict."""
    context: dict = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid variable format (expected KEY=VALUE): {pair}")
        key, _, value = pair.partition("=")
        context[key.strip()] = value
    return context


def run(args: argparse.Namespace) -> None:
    """Execute the render sub-command."""
    try:
        context = _parse_variables(args.variables)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        rendered = render_file(args.template, context)
    except RenderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w") as f:
            f.write(rendered)
    else:
        print(rendered, end="")
