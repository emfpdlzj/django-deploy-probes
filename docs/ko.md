# django-deploy-probes

이 문서는 [문서 홈](index.md)을 기반으로 한 한국어 빠른 시작 안내서입니다.

Django deployment probe endpoint를 제공합니다.

## 설치

```bash
pip install django-deploy-probes
```

지원 런타임은 Python 3.10–3.14와 Django 5.2 LTS, 6.0, 6.1입니다. Django 4.2가 필요한
프로젝트는 `0.3.x` 릴리스 계열을 사용하세요.

선택적으로 Redis, Celery, OpenAPI 연동을 extras로 설치할 수 있습니다. Storage check는
Django storage alias를 재사용하므로 별도 extra가 필요하지 않습니다.

```bash
pip install "django-deploy-probes[redis]"
pip install "django-deploy-probes[celery]"
pip install "django-deploy-probes[openapi]"
pip install "django-deploy-probes[all]"
```

## 빠른 시작

### Include 방식 URL 설정

```python
from django.urls import include, path

urlpatterns = [
    path("", include("django_deploy_probes.urls")),
]
```

### Import 방식 URL 설정

```python
from django.urls import path
from django_deploy_probes.views import healthz, readyz, startupz, version

urlpatterns = [
    path("healthz/", healthz),
    path("readyz/", readyz),
    path("startupz/", startupz),
    path("version/", version),
]
```

Include 방식은 `/healthz`, `/readyz`, `/startupz`, `/version`을 제공합니다. HTTP endpoint와
동일한 payload contract를 CLI에서도 사용할 수 있습니다.

```bash
python manage.py deploy_probes healthz --json
python manage.py deploy_probes readyz --json
python manage.py deploy_probes startupz --json
python manage.py deploy_probes version --json
```

Readiness 및 startup 사용자 정의 check 메시지는 기본적으로 숨겨집니다.
`EXPOSE_CHECK_MESSAGES=True`를 사용하는 경우 메시지에 secret이나 민감한 값을 포함하지
마세요.

Security check는 기본적으로 `REMOTE_ADDR`을 사용합니다. Trusted reverse proxy 뒤에서 probe에 접근하는 경우 `TRUSTED_PROXY_NETWORKS`와 `CLIENT_IP_HEADER`를 설정해 원래 client IP를 안전하게 판별하세요.

Storage check는 local filesystem, S3-compatible backend 및 Django `STORAGES`에 등록된 custom
backend를 검사할 수 있습니다. 자세한 설정은 [endpoint reference](api.md#storage-checks)를
참고하세요.

## 빌드 및 배포

### 빌드

```bash
uv build
```

생성된 distribution은 `dist/`에 기록됩니다.

생성 파일:

- `dist/django_deploy_probes-0.6.1.tar.gz`
- `dist/django_deploy_probes-0.6.1-py3-none-any.whl`

### 설치 테스트

빌드 후 clean environment에서 wheel을 설치해 확인합니다.

```bash
python -m venv /tmp/django-deploy-probes-install-test
source /tmp/django-deploy-probes-install-test/bin/activate
pip install dist/django_deploy_probes-0.6.1-py3-none-any.whl
python -c "import django_deploy_probes; print(django_deploy_probes.__version__)"
```

### PyPI 배포

GitHub Release를 발행하면 `.github/workflows/publish.yml`이 PyPI Trusted Publishing으로 배포합니다.

[영어 문서 홈으로 돌아가기](index.md)
