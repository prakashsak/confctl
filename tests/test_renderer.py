"""Tests for confctl.renderer module."""

import pytest

from confctl.renderer import (
    RenderError,
    extract_variables,
    load_template,
    render_file,
    render_template,
)


@pytest.fixture
def template_file(tmp_path):
    t = tmp_path / "config.tmpl"
    t.write_text("host={{ host }}\nport={{ port }}\nenv={{ env }}\n")
    return t


def test_load_template_returns_string(template_file):
    content = load_template(str(template_file))
    assert "host={{ host }}" in content


def test_load_template_missing_raises():
    with pytest.raises(RenderError, match="not found"):
        load_template("/nonexistent/template.tmpl")


def test_extract_variables_finds_all():
    template = "{{ host }}:{{ port }} # {{ host }}"
    variables = extract_variables(template)
    assert variables == ["host", "port"]


def test_extract_variables_empty_template():
    assert extract_variables("no variables here") == []


def test_extract_variables_whitespace_tolerant():
    template = "{{  host  }} and {{ port}}"
    assert extract_variables(template) == ["host", "port"]


def test_render_template_substitutes_values():
    template = "host={{ host }}\nport={{ port }}"
    result = render_template(template, {"host": "localhost", "port": 5432})
    assert result == "host=localhost\nport=5432"


def test_render_template_missing_variable_raises():
    template = "host={{ host }}\nuser={{ user }}"
    with pytest.raises(RenderError, match="user"):
        render_template(template, {"host": "localhost"})


def test_render_template_extra_context_ignored():
    template = "key={{ key }}"
    result = render_template(template, {"key": "value", "extra": "ignored"})
    assert result == "key=value"


def test_render_template_numeric_values():
    result = render_template("timeout={{ timeout }}", {"timeout": 30})
    assert result == "timeout=30"


def test_render_file_end_to_end(template_file):
    result = render_file(
        str(template_file),
        {"host": "db.example.com", "port": 5432, "env": "production"},
    )
    assert "host=db.example.com" in result
    assert "port=5432" in result
    assert "env=production" in result


def test_render_file_missing_template_raises():
    with pytest.raises(RenderError):
        render_file("/no/such/file.tmpl", {})
