# Basic Example

## Run

```bash
cd examples/basic
python -m venv .venv
source .venv/bin/activate
pip install django
pip install -e ../..
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

## Verify

```bash
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/readyz
curl -fsS http://127.0.0.1:8000/version
```

