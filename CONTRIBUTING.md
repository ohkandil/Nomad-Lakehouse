# Contributing

Thanks for contributing to Nomad Lakehouse.

## Principles

- Keep the project lightweight and local-first
- Preserve modular scripts and clear separation of concerns
- Prefer explicit, reproducible commands over hidden automation
- Maintain security checks as part of normal development flow
- Keep documentation in sync with every behavior change

## Local Development Setup

```bash
chmod +x scripts/*.sh
sudo ./scripts/setup_python_env.sh
source .venv/bin/activate
```

## Pull Request Checklist

Run these before opening a PR:

```bash
python3 -m ruff check .
python3 -m mypy scripts
python3 -m pytest
sudo ./scripts/security_scan.sh
```

For operational workflow changes, include updates to:

- `README.md`
- `docs/setup.md`
- `docs/ubuntu-deploy.md`
- `docs/week1-closure.md` (when Week 1 closure evidence is affected)

If `pip-audit` reports issues:

```bash
sudo ./scripts/remediate_python_vulns.sh
python3 -m pip_audit
```

## Commit Guidelines

- Keep commits focused and atomic
- Include docs updates for behavior changes
- Add or update tests when logic changes
- Use descriptive commit messages

## Security Expectations

- Never commit secrets or production credentials
- Keep `.env` local and version only `.env.example`
- Treat High/Critical security findings as release blockers
