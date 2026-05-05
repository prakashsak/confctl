"""Tests for confctl.migrator"""

from __future__ import annotations

import pytest
import yaml

from confctl.migrator import (
    MigrateError,
    dump_migrated,
    load_migration_rules,
    load_yaml_for_migrate,
    migrate_config,
)


@pytest.fixture()
def yaml_config(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("host: localhost\nport: 5432\ndebug: true\n")
    return cfg


@pytest.fixture()
def rules_file(tmp_path):
    rules = tmp_path / "rules.yaml"
    rules.write_text(
        "- action: rename\n  from: host\n  to: db_host\n"
        "- action: delete\n  key: debug\n"
        "- action: set_default\n  key: timeout\n  value: 30\n"
    )
    return rules


def test_load_yaml_for_migrate_returns_dict(yaml_config):
    data = load_yaml_for_migrate(str(yaml_config))
    assert isinstance(data, dict)
    assert data["host"] == "localhost"


def test_load_yaml_for_migrate_missing_raises(tmp_path):
    with pytest.raises(MigrateError, match="not found"):
        load_yaml_for_migrate(str(tmp_path / "missing.yaml"))


def test_load_yaml_for_migrate_empty_returns_empty(tmp_path):
    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    assert load_yaml_for_migrate(str(empty)) == {}


def test_load_yaml_for_migrate_non_mapping_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- item1\n- item2\n")
    with pytest.raises(MigrateError, match="mapping"):
        load_yaml_for_migrate(str(bad))


def test_load_migration_rules_returns_list(rules_file):
    rules = load_migration_rules(str(rules_file))
    assert isinstance(rules, list)
    assert len(rules) == 3


def test_load_migration_rules_missing_raises(tmp_path):
    with pytest.raises(MigrateError, match="not found"):
        load_migration_rules(str(tmp_path / "no_rules.yaml"))


def test_load_migration_rules_empty_returns_empty(tmp_path):
    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    assert load_migration_rules(str(empty)) == []


def test_migrate_config_rename(rules_file):
    data = {"host": "localhost", "port": 5432, "debug": True}
    rules = load_migration_rules(str(rules_file))
    result = migrate_config(data, rules)
    assert "db_host" in result
    assert "host" not in result


def test_migrate_config_delete(rules_file):
    data = {"host": "localhost", "port": 5432, "debug": True}
    rules = load_migration_rules(str(rules_file))
    result = migrate_config(data, rules)
    assert "debug" not in result


def test_migrate_config_set_default(rules_file):
    data = {"host": "localhost", "port": 5432, "debug": True}
    rules = load_migration_rules(str(rules_file))
    result = migrate_config(data, rules)
    assert result["timeout"] == 30


def test_migrate_config_set_default_does_not_overwrite(tmp_path):
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("- action: set_default\n  key: port\n  value: 9999\n")
    rules = load_migration_rules(str(rules_file))
    data = {"port": 5432}
    result = migrate_config(data, rules)
    assert result["port"] == 5432


def test_migrate_config_unknown_action_raises(tmp_path):
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text("- action: explode\n  key: x\n")
    rules = load_migration_rules(str(rules_file))
    with pytest.raises(MigrateError, match="Unknown migration action"):
        migrate_config({"x": 1}, rules)


def test_migrate_config_does_not_mutate_original(rules_file):
    original = {"host": "localhost", "debug": True}
    rules = load_migration_rules(str(rules_file))
    migrate_config(original, rules)
    assert "host" in original


def test_dump_migrated_returns_yaml_string():
    data = {"db_host": "localhost", "port": 5432}
    result = dump_migrated(data)
    assert isinstance(result, str)
    parsed = yaml.safe_load(result)
    assert parsed == data
