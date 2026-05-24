# Security Policy

## Supported versions

Security fixes are provided for the latest released minor version.

## Reporting a vulnerability

Please report suspected vulnerabilities privately by email to the package maintainer listed in
`pyproject.toml`.

Do not open a public issue for security-sensitive reports.

## Security defaults

- `/healthz` is intentionally minimal and does not check external dependencies.
- `/startupz`, `/readyz`, and `/version` can be protected with internal IP checks or a probe token.
- `X-Forwarded-For` is not trusted by default.
- Custom check messages are hidden unless `EXPOSE_CHECK_MESSAGES=True`.
- Safe failure reasons are hidden unless `DETAIL_LEVEL="safe"`.
