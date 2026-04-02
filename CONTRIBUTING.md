# Contributing

## Development Setup

1. Use Ubuntu 24.04 LTS (recommended) or compatible Linux environment.
1. Run dependency bootstrap with `sudo ./scripts/setup_python_env.sh`.
1. Activate the environment with `source .venv/bin/activate`.

## Before Opening a PR

- Run lint and type checks:
  - `ruff check .`
  - `mypy scripts`
- Run tests:
  - `pytest`
- Run security checks:
  - `sudo ./scripts/security_scan.sh`

## Security Expectations

- Never commit real secrets or production credentials.
- Keep `.env` local and update `.env.example` when adding config.
- Prefer dependency versions with known vulnerability fixes.
