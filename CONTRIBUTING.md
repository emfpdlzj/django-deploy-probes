# Contributing

Thanks for helping improve `django-deploy-probes`.

## Local setup

```bash
uv sync --dev
uv run pre-commit install
uv run pre-commit run --all-files
uv run pytest -q
uv run ruff check .
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
3. Run tests, lint, and build locally.
4. Merge the version bump PR into `main`. This creates a draft GitHub release and tag automatically.
5. Review and publish the draft GitHub release. The publish workflow uses PyPI Trusted Publishing.
