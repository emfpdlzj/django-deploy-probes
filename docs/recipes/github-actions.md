# GitHub Actions Deployment Validation

This recipe validates a deployed Django service before continuing a rollout.

```yaml
name: Deploy Validation

on:
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Check liveness
        run: curl -fsS "$APP_URL/healthz"
        env:
          APP_URL: ${{ vars.APP_URL }}

      - name: Check startup
        run: curl -fsS -H "X-Probe-Token: $PROBE_TOKEN" "$APP_URL/startupz"
        env:
          APP_URL: ${{ vars.APP_URL }}
          PROBE_TOKEN: ${{ secrets.PROBE_TOKEN }}

      - name: Check readiness
        run: curl -fsS -H "X-Probe-Token: $PROBE_TOKEN" "$APP_URL/readyz"
        env:
          APP_URL: ${{ vars.APP_URL }}
          PROBE_TOKEN: ${{ secrets.PROBE_TOKEN }}

      - name: Check version
        run: |
          response="$(curl -fsS -H "X-Probe-Token: $PROBE_TOKEN" "$APP_URL/version")"
          echo "$response"
          echo "$response" | grep "\"version\":\"$APP_VERSION\""
        env:
          APP_URL: ${{ vars.APP_URL }}
          APP_VERSION: ${{ github.sha }}
          PROBE_TOKEN: ${{ secrets.PROBE_TOKEN }}
```

Use token protection for `/readyz`, `/startupz`, and `/version` when validating a public URL.
