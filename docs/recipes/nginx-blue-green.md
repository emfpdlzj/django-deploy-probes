# Nginx Blue-Green Switching

This recipe validates the inactive slot before switching upstream traffic.

```bash
set -euo pipefail

NEXT_SLOT_URL="http://127.0.0.1:8002"

curl -fsS "$NEXT_SLOT_URL/healthz"
curl -fsS -H "X-Probe-Token: $PROBE_TOKEN" "$NEXT_SLOT_URL/startupz"
curl -fsS -H "X-Probe-Token: $PROBE_TOKEN" "$NEXT_SLOT_URL/readyz"
curl -fsS -H "X-Probe-Token: $PROBE_TOKEN" "$NEXT_SLOT_URL/version"

sudo ln -sfn /etc/nginx/upstreams/green.conf /etc/nginx/conf.d/current-upstream.conf
sudo nginx -t
sudo systemctl reload nginx
```

Keep `/healthz` light and avoid enabling dependency checks there. Use `/readyz` for dependency validation before traffic moves.
