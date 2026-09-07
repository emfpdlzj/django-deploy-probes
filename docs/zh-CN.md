# django-deploy-probes

本文档是基于 [文档首页](index.md) 的简体中文快速入门指南。

为 Django 提供 deployment probe endpoints。

## 安装

```bash
pip install django-deploy-probes
```

支持的运行环境为 Python 3.10–3.14 以及 Django 5.2 LTS、6.0、6.1。仍需要 Django 4.2
的项目应使用 `0.3.x` 发布系列。

Redis、Celery 和 OpenAPI 集成可以通过 extras 选择安装。Storage check 复用 Django storage
alias，因此不需要额外的 extra。

```bash
pip install "django-deploy-probes[redis]"
pip install "django-deploy-probes[celery]"
pip install "django-deploy-probes[openapi]"
pip install "django-deploy-probes[all]"
```

## 快速开始

### Include 风格的 URL 配置

```python
from django.urls import include, path

urlpatterns = [
    path("", include("django_deploy_probes.urls")),
]
```

### Import 风格的 URL 配置

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

Include 风格会提供 `/healthz`、`/readyz`、`/startupz` 和 `/version`。也可以通过 CLI
使用与 HTTP endpoint 相同的 payload contract。

```bash
python manage.py deploy_probes healthz --json
python manage.py deploy_probes readyz --json
python manage.py deploy_probes startupz --json
python manage.py deploy_probes version --json
```

Readiness 和 startup 自定义 check 消息默认隐藏。使用 `EXPOSE_CHECK_MESSAGES=True` 时，请勿在
消息中包含 secrets 或敏感值。

Security checks 默认使用 `REMOTE_ADDR`。如果 probes 位于 trusted reverse proxy 后面，请配置 `TRUSTED_PROXY_NETWORKS` 和 `CLIENT_IP_HEADER`，以安全地识别原始 client IP。

Storage check 可以检查 local filesystem、S3-compatible backend，以及注册到 Django
`STORAGES` 的 custom backend。详细配置请参阅 [endpoint reference](api.md#storage-checks)。

## 构建与发布

### 构建

```bash
uv build
```

生成的 distributions 会写入 `dist/`。

生成文件：

- `dist/django_deploy_probes-0.6.1.tar.gz`
- `dist/django_deploy_probes-0.6.1-py3-none-any.whl`

### 安装测试

构建完成后，在 clean environment 中安装 wheel 进行验证：

```bash
python -m venv /tmp/django-deploy-probes-install-test
source /tmp/django-deploy-probes-install-test/bin/activate
pip install dist/django_deploy_probes-0.6.1-py3-none-any.whl
python -c "import django_deploy_probes; print(django_deploy_probes.__version__)"
```

### 发布到 PyPI

发布 GitHub Release 后，`.github/workflows/publish.yml` 会通过 PyPI Trusted Publishing 发布。

[返回英文文档首页](index.md)
