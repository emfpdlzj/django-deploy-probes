# django-deploy-probes

本文档是 [文档首页](index.md) 的简体中文翻译。

为 Django 提供 deployment probe endpoints。

## 安装

```bash
pip install django-deploy-probes
```

可选的 Redis 和 Celery readiness checks 可以通过 extras 安装：

```bash
pip install "django-deploy-probes[redis]"
pip install "django-deploy-probes[celery]"
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

`/readyz` 的自定义 check 消息默认隐藏。使用 `EXPOSE_CHECK_MESSAGES=True` 时，请不要在消息中包含 secrets 或敏感值。

Security checks 默认使用 `REMOTE_ADDR`，并且不信任 `X-Forwarded-For`。如果通过 proxy 访问 probes，请单独配置 reverse proxy。

## 构建与发布

### 构建

```bash
uv build
```

生成的 distributions 会写入 `dist/`。

生成文件：

- `dist/django_deploy_probes-0.1.0.tar.gz`
- `dist/django_deploy_probes-0.1.0-py3-none-any.whl`

### 安装测试

构建完成后，在 clean environment 中安装 wheel 进行验证：

```bash
python -m venv /tmp/django-deploy-probes-install-test
source /tmp/django-deploy-probes-install-test/bin/activate
pip install dist/django_deploy_probes-0.1.0-py3-none-any.whl
python -c "import django_deploy_probes; print(django_deploy_probes.__version__)"
```

### 发布到 PyPI

发布 GitHub Release 后，`.github/workflows/publish.yml` 会通过 PyPI Trusted Publishing 发布。

[返回英文文档首页](index.md)
