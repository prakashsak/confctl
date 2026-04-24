"""Template rendering for config files using Jinja2-style variable substitution."""

import re
from typing import Any


class RenderError(Exception):
    """Raised when template rendering fails."""


def load_template(path: str) -> str:
    """Load a template file and return its content as a string."""
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        raise RenderError(f"Template file not found: {path}")


def extract_variables(template: str) -> list[str]:
    """Return a sorted list of unique variable names found in the template."""
    pattern = re.compile(r"\{\{\s*(\w+)\s*\}\}")
    return sorted(set(pattern.findall(template)))


def render_template(template: str, context: dict[str, Any]) -> str:
    """Replace {{ var }} placeholders in template with values from context.

    Raises RenderError if any variable in the template is missing from context.
    """
    variables = extract_variables(template)
    missing = [v for v in variables if v not in context]
    if missing:
        raise RenderError(
            f"Missing template variables: {', '.join(missing)}"
        )

    def replacer(match: re.Match) -> str:
        key = match.group(1).strip()
        return str(context[key])

    return re.sub(r"\{\{\s*(\w+)\s*\}\}", replacer, template)


def render_file(template_path: str, context: dict[str, Any]) -> str:
    """Load a template from disk and render it with the given context."""
    template = load_template(template_path)
    return render_template(template, context)
