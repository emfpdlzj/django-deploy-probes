# Kubernetes Probes

## Goal

Use `/healthz` as a liveness probe, `/startupz` as a startup probe, and `/readyz` as a readiness probe.

## Final Result

Kubernetes waits for startup checks, restarts dead containers, and removes not-ready pods from Service traffic.

## File Structure

```text
kubernetes/
  deployment.yaml
  service.yaml
```

## Install

```bash
docker build -t registry.example.com/my-django-app:0.1.0 .
docker push registry.example.com/my-django-app:0.1.0
```

## Full Code

`deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-django-app
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: my-django-app
  template:
    metadata:
      labels:
        app: my-django-app
    spec:
      containers:
        - name: web
          image: registry.example.com/my-django-app:0.1.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
          env:
            - name: DJANGO_ENV
              value: prod
            - name: APP_VERSION
              value: 0.1.0
            - name: GIT_COMMIT
              value: a1b2c3d
            - name: GIT_BRANCH
              value: main
            - name: BUILD_TIME
              value: "2026-05-17T00:00:00+09:00"
            - name: DEPLOY_SLOT
              value: rolling
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 2
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /startupz
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 12
          readinessProbe:
            httpGet:
              path: /readyz
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 2
```

`service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-django-app
spec:
  selector:
    app: my-django-app
  ports:
    - name: http
      port: 80
      targetPort: 8000
```

## Run

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Verify

```bash
kubectl rollout status deployment/my-django-app
kubectl get pods -l app=my-django-app
kubectl port-forward service/my-django-app 8000:80
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/startupz
curl -fsS http://127.0.0.1:8000/readyz
curl -fsS http://127.0.0.1:8000/version
```

## Failure Checks

If a pod is not ready:

```bash
kubectl describe pod -l app=my-django-app
kubectl logs -l app=my-django-app --tail=100
```

If `/readyz` returns `503`, inspect the dependency check results:

```bash
kubectl port-forward service/my-django-app 8000:80
curl -i http://127.0.0.1:8000/readyz
```

## Next Step

Use [Security options](security.md) to restrict `/startupz`, `/readyz`, and `/version`.
