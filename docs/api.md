# API Reference

## Endpoints

`GET /healthz`

Returns process liveness only. It must not touch databases, caches, Redis, Celery, or external services.

```json
{
  "status": "ok"
}
```

`GET /readyz`

Returns deployment readiness. Configure checks with `DEPLOY_PROBES["READY_CHECKS"]`.

```json
{
  "status": "ready",
  "checks": {
    "database.default": "ok",
    "redis.default": "ok"
  }
}
```

`GET /startupz`

Returns startup/bootstrap readiness. Configure checks with `DEPLOY_PROBES["STARTUP_CHECKS"]`.
This endpoint is useful for Kubernetes `startupProbe` or deployment bootstrap validation.

```json
{
  "status": "started",
  "checks": {
    "migrations": "ok"
  }
}
```

`GET /version`

Returns deployment metadata. Build details are hidden unless `EXPOSE_BUILD_INFO=True`.

```json
{
  "service": "my-django-app",
  "environment": "prod",
  "version": "1.2.0"
}
```

## Management Command

Run the same probes without going through HTTP:

```bash
python manage.py deploy_probes healthz --json
python manage.py deploy_probes readyz --json
python manage.py deploy_probes startupz --json
python manage.py deploy_probes version --json
```

The CLI uses the same JSON payload contract as the HTTP endpoints. This makes it practical for CI/CD jobs, prestart hooks, and local debugging without changing parsers between environments.

Exit codes:

- `0`: probe passed
- `1`: probe failed
- `2`: invalid arguments or invalid Django/probe settings
- `3`: unexpected execution failure

## Settings

```python
DEPLOY_PROBES = {
    "SERVICE_NAME": "django-app",
    "ENVIRONMENT": "local",
    "VERSION": "unknown",
    "COMMIT": "unknown",
    "BRANCH": "unknown",
    "BUILD_TIME": "unknown",
    "SLOT": "unknown",
    "READY_CHECKS": [],
    "STARTUP_CHECKS": [],
    "DATABASES": ["default"],
    "STORAGE": {},
    "REDIS": {},
    "CELERY": {
        "BROKER": False,
        "WORKERS": False,
        "RESULT_BACKEND": False,
        "TIMEOUT": 1.0,
    },
    "MIGRATIONS": {
        "DATABASE": "default",
    },
    "READY_CUSTOM_CHECKS": [],
    "STARTUP_CUSTOM_CHECKS": [],
    "DETAIL_LEVEL": "none",
    "INCLUDE_CHECK_DURATIONS": False,
    "REQUIRE_READY_CHECKS": False,
    "REQUIRE_STARTUP_CHECKS": False,
    "EXPOSE_CHECK_MESSAGES": False,
    "EXPOSE_VERSION": True,
    "EXPOSE_BUILD_INFO": False,
    "INTERNAL_IP_ONLY": False,
    "INTERNAL_IP_NETWORKS": [
        "127.0.0.1/32",
        "::1/128",
        "10.0.0.0/8",
    ],
    "TRUSTED_PROXY_NETWORKS": [],
    "CLIENT_IP_HEADER": None,
    "HEADER_TOKEN_VALIDATION": False,
    "ENABLE_OPENAPI": False,
}
```

## Check Results

By default, check values are compact strings:

```json
{
  "database.default": "ok"
}
```

With `DETAIL_LEVEL="safe"`, failures include stable safe reasons:

```json
{
  "redis.default": {
    "status": "fail",
    "reason": "redis_package_missing"
  }
}
```

With `INCLUDE_CHECK_DURATIONS=True`, every check is wrapped with `status` and `duration_ms`:

```json
{
  "database.default": {
    "status": "ok",
    "duration_ms": 0.42
  }
}
```

## Storage Checks

The builtin `storage` check uses Django storage aliases from `STORAGES`. That means the same probe works for local filesystem storage, S3 backends, and custom storage implementations that honor Django's storage API.

Example configuration:

```python
DEPLOY_PROBES = {
    "READY_CHECKS": ["storage"],
    "STORAGE": {
        "default": {
            "CHECK": "exists",
            "PATH": "probes/ready.txt",
        },
        "s3_media": {
            "CHECK": "write",
            "PREFIX": "deploy-probes",
        },
    },
}
```

Available modes:

- `exists`: calls `storage.exists(PATH)` and fails when the object is missing.
- `write`: creates and deletes a temporary probe object under `PREFIX`.

If you only want to confirm that the backend responds without requiring a sentinel object, set `ALLOW_MISSING=True` on an `exists` check.

## Setting Validation

The package registers Django system checks. Run this before deployment:

```bash
python manage.py check
```

`CUSTOM_CHECKS` is still accepted as a legacy alias for readiness checks. Prefer
`READY_CUSTOM_CHECKS` and `STARTUP_CUSTOM_CHECKS` for new projects so readiness and
startup behavior stay independent.

Validation catches common mistakes such as unknown check names, invalid custom check lists, invalid CIDR ranges, missing Redis locations, invalid `DETAIL_LEVEL`, and missing probe tokens.

When probes are accessed through a trusted reverse proxy, set `TRUSTED_PROXY_NETWORKS` and
`CLIENT_IP_HEADER` so `INTERNAL_IP_ONLY` can evaluate the original client IP instead of the
proxy hop. `X-Forwarded-For` is resolved by walking the proxy chain from right to left and
selecting the last untrusted address as the client IP.
