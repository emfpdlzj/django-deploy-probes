# Kubernetes Example

## Run

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Verify

```bash
kubectl rollout status deployment/my-django-app
kubectl port-forward service/my-django-app 8000:80
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/readyz
```

