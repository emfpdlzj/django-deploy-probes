# AWS ECS and ALB Health Checks

For an ALB target group, use `/healthz` as the public health check path:

```text
Health check path: /healthz
Success codes: 200
Timeout: 5 seconds
Interval: 30 seconds
Healthy threshold: 2
Unhealthy threshold: 3
```

Use `/readyz` in deployment automation before changing traffic weights:

```bash
curl -fsS -H "X-Probe-Token: $PROBE_TOKEN" "https://app.example.com/readyz"
curl -fsS -H "X-Probe-Token: $PROBE_TOKEN" "https://app.example.com/version"
```

Recommended settings:

```python
DEPLOY_PROBES = {
    "READY_CHECKS": ["database", "redis"],
    "HEADER_TOKEN_VALIDATION": {
        "HEADER_NAME": "X-Probe-Token",
        "TOKEN": os.environ["PROBE_TOKEN"],
        "PROTECT_HEALTHZ": False,
    },
}
```

Do not put secrets in custom check messages. Keep `EXPOSE_CHECK_MESSAGES=False` unless the endpoint is internal and tightly controlled.
