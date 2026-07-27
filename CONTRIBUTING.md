# Contributing

Thanks for helping improve `django-deploy-probes`.

The current development branch targets Python 3.10 through 3.14 and Django 5.2 LTS
and 6.0.

## Local setup

```bash
uv sync --dev
uv run pre-commit install
uv run pre-commit run --all-files
uv run pytest -q
uv run ruff check .
uv run mkdocs build --strict
uv build
```

## Development guidelines

- Keep `/healthz` lightweight. It must not touch databases, caches, Redis, Celery, or external services.
- Keep readiness failures secret-safe by default.
- Add or update tests for behavior changes.
- Update README or docs when public settings, endpoints, or response shapes change.

## Release checklist

1. Update the version in `django_deploy_probes/__init__.py`.
2. Update `CHANGELOG.md`.
3. Run tests, lint, docs build, and build locally.
4. Smoke-install the built wheel in a clean virtualenv.
5. Merge the version bump PR into `main`. This creates a draft GitHub release and tag automatically.
6. Review and publish the draft GitHub release. The publish workflow uses PyPI Trusted Publishing.
