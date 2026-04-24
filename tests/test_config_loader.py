"""Tests for confctl.config_loader module."""

import pytest
from pathlib import Path

from confctl.config_loader import (
    discover_configs,
    group_by_environment,
    load_env_configs,
)


@pytest.fixture()
def config_tree(tmp_path: Path) -> Path:
    """Create a temporary directory tree with sample config files."""
    (tmp_path / "prod").mkdir()
    (tmp_path / "staging").mkdir()
    (tmp_path / "prod" / "app.env").write_text("DB_HOST=prod-db\nDEBUG=false\n")
    (tmp_path / "prod" / "cache.cfg").write_text("[cache]\nttl=300\n")
    (tmp_path / "staging" / "app.env").write_text("DB_HOST=staging-db\nDEBUG=true\n")
    (tmp_path / "staging" / "README.md").write_text("# ignored")
    return tmp_path


# --- discover_configs ---

def test_discover_configs_finds_known_extensions(config_tree: Path):
    files = discover_configs(str(config_tree))
    basenames = [Path(f).name for f in files]
    assert "app.env" in basenames
    assert "cache.cfg" in basenames


def test_discover_configs_excludes_non_config_files(config_tree: Path):
    files = discover_configs(str(config_tree))
    basenames = [Path(f).name for f in files]
    assert "README.md" not in basenames


def test_discover_configs_returns_sorted(config_tree: Path):
    files = discover_configs(str(config_tree))
    assert files == sorted(files)


def test_discover_configs_missing_dir_raises():
    with pytest.raises(FileNotFoundError):
        discover_configs("/nonexistent/path/xyz")


def test_discover_configs_file_path_raises(tmp_path: Path):
    a_file = tmp_path / "single.env"
    a_file.write_text("KEY=val")
    with pytest.raises(NotADirectoryError):
        discover_configs(str(a_file))


def test_discover_configs_custom_extension(config_tree: Path):
    files = discover_configs(str(config_tree), extensions=(".cfg",))
    assert all(f.endswith(".cfg") for f in files)
    assert len(files) == 1


# --- group_by_environment ---

def test_group_by_environment_splits_by_subdir(config_tree: Path):
    files = discover_configs(str(config_tree))
    groups = group_by_environment(files, env_names=["prod", "staging"])
    assert "prod" in groups
    assert "staging" in groups
    assert all("prod" in p for p in groups["prod"])


def test_group_by_environment_unknown_env_goes_to_default():
    paths = ["/some/unknown/app.env"]
    groups = group_by_environment(paths, env_names=["prod"])
    assert "default" in groups


def test_group_by_environment_no_env_names_uses_any_subdir(config_tree: Path):
    files = discover_configs(str(config_tree))
    groups = group_by_environment(files)
    # Should have at least prod and staging as keys
    assert len(groups) >= 2


# --- load_env_configs ---

def test_load_env_configs_returns_lines(config_tree: Path):
    configs = load_env_configs(str(config_tree), "prod")
    assert "app.env" in configs
    assert any("DB_HOST=prod-db" in line for line in configs["app.env"])


def test_load_env_configs_missing_env_raises(config_tree: Path):
    with pytest.raises(FileNotFoundError):
        load_env_configs(str(config_tree), "nonexistent")


def test_load_env_configs_all_files_present(config_tree: Path):
    configs = load_env_configs(str(config_tree), "prod")
    assert "cache.cfg" in configs
    assert len(configs) == 2
