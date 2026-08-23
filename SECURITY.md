# Security Policy

## Supported versions

| Release | Python | Django | Security support |
| --- | --- | --- | --- |
| 0.6.x | 3.10–3.14 | 5.2 LTS, 6.0, 6.1 | Supported |
| 0.5.x | 3.10–3.14 | 5.2 LTS, 6.0 | Ended |
| 0.4.x | 3.10–3.14 | 5.2 LTS, 6.0 | Ended |
| 0.3.x | 3.9–3.14 | 4.2–5.2 | Ended |

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
