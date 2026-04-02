# Contributing

## Development Setup
1. Use Ubuntu 24.04 LTS (recommended) or compatible Linux environment.
2. Create and activate a Python 3.11 virtual environment.
3. Install dependencies:
   - `pip install -e .[dev]`

## Before Opening a PR
- Run lint and type checks:
  - `ruff check .`
  - `mypy scripts`
- Run tests:
  - `pytest`
- Run security checks:
  - `./scripts/security_scan.sh`

## Security Expectations
- Never commit real secrets or production credentials.
- Keep `.env` local and update `.env.example` when adding config.
- Prefer dependency versions with known vulnerability fixes.
