# Security Example

## Run

```bash
cd examples/security
python -m venv .venv
source .venv/bin/activate
pip install django
pip install -e ../..
python manage.py migrate
PROBE_TOKEN=local-probe-token python manage.py runserver 127.0.0.1:8000
```

## Verify

```bash
curl -i http://127.0.0.1:8000/version
curl -fsS -H "X-Probe-Token: local-probe-token" http://127.0.0.1:8000/version
```

