# driftwatch

A lightweight CLI tool to detect schema drift between SQL databases and ORM model definitions.

---

## Installation

```bash
pip install driftwatch
```

Or install from source:

```bash
git clone https://github.com/yourname/driftwatch.git
cd driftwatch && pip install -e .
```

---

## Usage

Point `driftwatch` at your database and your ORM models to detect any drift:

```bash
driftwatch check --db postgresql://user:pass@localhost/mydb --models myapp.models
```

Example output:

```
[✓] users         — in sync
[✗] orders        — missing column: shipped_at (defined in model, not in DB)
[✗] products      — extra column: legacy_code (in DB, not in model)

2 drift(s) detected.
```

### Options

| Flag | Description |
|------|-------------|
| `--db` | Database connection URL |
| `--models` | Python module path to ORM models |
| `--format` | Output format: `text` (default) or `json` |
| `--strict` | Exit with code 1 if any drift is found |

Run `driftwatch --help` for the full list of options.

---

## Supported ORMs

- SQLAlchemy
- Django ORM *(coming soon)*

---

## License

This project is licensed under the [MIT License](LICENSE).