# Docker Compose Example

## Run

```bash
cd examples/docker-compose
docker compose up --build
```

## Verify

```bash
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/readyz
curl -fsS http://127.0.0.1:8000/version
```

## Failure Check

```bash
docker compose stop redis
curl -i http://127.0.0.1:8000/readyz
docker compose start redis
```

