# Production Operations Guide

This guide turns probe configuration into a repeatable deployment gate. It complements the
platform-specific Docker, Kubernetes, and load balancer examples.

## Assign One Decision to Each Probe

| Probe | Decision | Must not do |
| --- | --- | --- |
| `/healthz` | Should the process be restarted? | Query a database, cache, broker, or remote service. |
| `/startupz` | Has this instance completed startup requirements? | Replace deployment automation or run migrations. |
| `/readyz` | Can this instance receive traffic now? | Perform slow diagnostics or optional business checks. |
| `/version` | Is the expected build or slot running? | Expose sensitive build data to untrusted networks. |

A dependency outage should normally remove an instance from traffic through `/readyz`; it should
not create a restart loop through `/healthz`.

## Pre-deployment Gate

Run configuration validation before contacting dependencies:

```bash
python manage.py check
```

The system check rejects unknown or duplicate checks, invalid aliases and types, incomplete Redis,
Celery, migration, storage, proxy, token, and OpenAPI settings, and configurations that would run a
Celery check without checking any Celery operation.

Run the in-process probes in the same image that will be deployed:

```bash
python manage.py deploy_probes startupz --json
python manage.py deploy_probes readyz --json
python manage.py deploy_probes version --json
```

After starting the instance, verify the HTTP path that the platform will call:

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/healthz
curl --fail --silent --show-error http://127.0.0.1:8000/startupz
curl --fail --silent --show-error http://127.0.0.1:8000/readyz
```

For blue-green or canary deployment, compare `/version` with the expected immutable image version
or commit before moving traffic. Do not accept only a successful status code when verifying a build.

## Timeout Budget

Checks execute sequentially. Set each dependency's native timeout first, then set the platform
timeout above the worst-case sum:

```text
platform timeout > database + Redis + Celery + storage + custom checks + network margin
```

Example for a readiness probe with a 1-second Redis timeout, a 1-second Celery broker timeout,
a 2-second database statement timeout, and a 2-second storage read timeout:

```text
worst-case checks = 1 + 1 + 2 + 2 = 6 seconds
recommended platform timeout = 7 or 8 seconds
```

Configure database limits in Django's database backend. For PostgreSQL, a deployment can use driver
connection and server-side statement timeouts:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "app",
        "USER": "app",
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ["DB_HOST"],
        "OPTIONS": {
            "connect_timeout": 2,
            "options": "-c statement_timeout=2000",
        },
    }
}
```

Configure connect/read limits in the storage backend and result backend transport. Returning from
an HTTP request cannot safely cancel arbitrary synchronous backend or custom-check work.

## Dependency Selection

Include only dependencies required to serve this instance's traffic:

```python
DEPLOY_PROBES = {
    "READY_CHECKS": ["database", "redis", "storage"],
    "STARTUP_CHECKS": ["migrations"],
    "DATABASES": ["default"],
    "REDIS": {
        "default": {
            "LOCATION": os.environ["REDIS_URL"],
            "TIMEOUT": 1.0,
        }
    },
    "STORAGE": {
        "media": {
            "CHECK": "exists",
            "PATH": "probes/ready.txt",
        }
    },
    "REQUIRE_READY_CHECKS": True,
    "REQUIRE_STARTUP_CHECKS": True,
}
```

Prefer a managed sentinel object for S3-style storage when readiness callers are frequent. A write
probe validates write and delete permission but creates more backend traffic and requires cleanup
permission.

## Security Checklist

- Keep `/readyz`, `/startupz`, and `/version` on an internal route or protect them with a token.
- Configure `TRUSTED_PROXY_NETWORKS` before trusting a forwarded client-IP header.
- Leave `EXPOSE_CHECK_MESSAGES=False` unless every message is reviewed for secrets.
- Leave `EXPOSE_BUILD_INFO=False` on public endpoints.
- Use `DETAIL_LEVEL="safe"` only when stable failure reasons are operationally useful.
- Mark probe paths as non-cacheable at every proxy or CDN layer; the Django responses already emit
  non-cache headers.
- Rotate the probe token like any other deployment secret.

See [configuration and security](security.md) for complete examples.

## Failure Drills

Test failure behavior before relying on a probe for automated traffic changes:

1. Block the database connection and confirm `/readyz` returns `503` while `/healthz` stays `200`.
2. Remove or rename an S3 sentinel and confirm only the storage check fails.
3. Stop Redis or the Celery broker and confirm the failure stays within the configured timeout.
4. Add an unapplied test migration and confirm `/startupz` returns `503`.
5. Send a forged `X-Forwarded-For` value from an untrusted source and confirm it is ignored.
6. Deploy an unexpected version and confirm the release gate rejects the `/version` payload.

Record the expected status code, maximum response time, and rollback action for each drill.

## Verified Backends

The project CI runs the probe code against PostgreSQL, Redis, a Redis-backed Celery broker and
result backend, filesystem storage, and MinIO as an S3-compatible Django storage backend. Unit tests
cover failure normalization, proxy handling, response contracts, and configuration errors across
the supported Python and Django matrix.
