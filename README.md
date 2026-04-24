# confctl

A lightweight CLI tool for managing and diffing environment-specific config files across deployments.

---

## Installation

```bash
pip install confctl
```

Or install from source:

```bash
git clone https://github.com/yourname/confctl.git && cd confctl && pip install -e .
```

---

## Usage

```bash
# Compare config files between two environments
confctl diff staging production

# Apply a config for a specific environment
confctl apply --env production --config ./configs/app.yaml

# List all tracked config files
confctl list

# Validate a config file against a schema
confctl validate --env staging --config ./configs/app.yaml
```

### Example

```bash
$ confctl diff staging production
~ database.host: db-staging.internal → db-prod.internal
~ cache.ttl: 300 → 600
+ feature_flags.new_ui: true
```

---

## Configuration

`confctl` looks for a `confctl.toml` file in the project root to define environments and config paths:

```toml
[environments]
staging = "./configs/staging"
production = "./configs/production"
```

---

## Requirements

- Python 3.8+

---

## License

This project is licensed under the [MIT License](LICENSE).