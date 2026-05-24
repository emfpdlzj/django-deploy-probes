# Docker Example

## Run

```bash
docker build -f examples/docker/Dockerfile -t django-deploy-probes-docker-example .
docker run --rm -p 8000:8000 django-deploy-probes-docker-example
```

## Verify

```bash
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/readyz
curl -fsS http://127.0.0.1:8000/version
```
