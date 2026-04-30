"""Tests for confctl.profiler."""

import pytest
import yaml
from pathlib import Path

from confctl.profiler import (
    ProfileError,
    load_yaml_profile,
    compare_profiles,
    format_profile_summary,
)


@pytest.fixture
def profile_files(tmp_path: Path):
    base = tmp_path / "base.yaml"
    base.write_text(yaml.dump({"host": "localhost", "port": 5432, "debug": True}))
    target = tmp_path / "target.yaml"
    target.write_text(yaml.dump({"host": "prod.example.com", "port": 5432, "workers": 4}))
    return base, target


def test_load_yaml_profile_returns_dict(profile_files):
    base, _ = profile_files
    data = load_yaml_profile(str(base))
    assert isinstance(data, dict)
    assert data["host"] == "localhost"


def test_load_yaml_profile_missing_raises(tmp_path):
    with pytest.raises(ProfileError, match="File not found"):
        load_yaml_profile(str(tmp_path / "ghost.yaml"))


def test_load_yaml_profile_empty_returns_empty(tmp_path):
    f = tmp_path / "empty.yaml"
    f.write_text("")
    assert load_yaml_profile(str(f)) == {}


def test_load_yaml_profile_non_mapping_raises(tmp_path):
    f = tmp_path / "list.yaml"
    f.write_text("- a\n- b\n")
    with pytest.raises(ProfileError, match="Expected a YAML mapping"):
        load_yaml_profile(str(f))


def test_compare_profiles_detects_added():
    base = {"host": "localhost"}
    target = {"host": "localhost", "workers": 4}
    result = compare_profiles(base, target)
    assert "workers" in result["added"]
    assert result["added"]["workers"] == 4


def test_compare_profiles_detects_removed():
    base = {"host": "localhost", "debug": True}
    target = {"host": "localhost"}
    result = compare_profiles(base, target)
    assert "debug" in result["removed"]


def test_compare_profiles_detects_changed():
    base = {"host": "localhost"}
    target = {"host": "prod.example.com"}
    result = compare_profiles(base, target)
    assert "host" in result["changed"]
    assert result["changed"]["host"] == ("localhost", "prod.example.com")


def test_compare_profiles_detects_unchanged():
    base = {"port": 5432}
    target = {"port": 5432}
    result = compare_profiles(base, target)
    assert "port" in result["unchanged"]


def test_compare_profiles_empty_dicts():
    result = compare_profiles({}, {})
    assert result["added"] == {}
    assert result["removed"] == {}
    assert result["changed"] == {}
    assert result["unchanged"] == []


def test_compare_profiles_result_keys_are_complete():
    """Ensure compare_profiles always returns all four expected keys."""
    result = compare_profiles({"a": 1}, {"b": 2})
    assert set(result.keys()) == {"added", "removed", "changed", "unchanged"}


def test_format_profile_summary_no_diff():
    summary = {"added": {}, "removed": {}, "changed": {}, "unchanged": ["port"]}
    out = format_profile_summary(summary, color=False)
    assert "unchanged" in out


def test_format_profile_summary_shows_all_categories():
    summary = {
        "added": {"workers": 4},
        "removed": {"debug": True},
        "changed": {"host": ("localhost", "prod")},
        "unchanged": ["port"],
    }
    out = format_profile_summary(summary, color=False)
    assert "+ workers" in out
    assert "- debug" in out


def test_format_profile_summary_changed_shows_both_values():
    """Verify that a changed key displays both the old and new values."""
    summary = {
        "added": {},
        "removed": {},
        "changed": {"host": ("localhost", "prod.example.com")},
        "unchanged": [],
    }
    out = format_profile_summary(summary, color=False)
    assert "localhost" in out
    assert "prod.example.com" in out
