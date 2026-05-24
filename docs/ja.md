# django-deploy-probes

このドキュメントは [README.md](../README.md) の日本語訳です。

Django deployment probe endpoint を提供します。

## インストール

```bash
pip install django-deploy-probes
```

Redis と Celery の readiness check は、extras として必要に応じてインストールできます。

```bash
pip install "django-deploy-probes[redis]"
pip install "django-deploy-probes[celery]"
pip install "django-deploy-probes[all]"
```

## クイックスタート

### Include 方式の URL 設定

```python
from django.urls import include, path

urlpatterns = [
    path("", include("django_deploy_probes.urls")),
]
```

### Import 方式の URL 設定

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

`/readyz` のカスタム check メッセージはデフォルトで非表示です。`EXPOSE_CHECK_MESSAGES=True` を使う場合は、secret や機密情報をメッセージに含めないでください。

Security check はデフォルトで `REMOTE_ADDR` を使用し、`X-Forwarded-For` は信頼しません。Proxy 経由で probe にアクセスする場合は、reverse proxy を別途設定してください。

## ビルドと公開

### ビルド

```bash
uv build
```

生成された distribution は `dist/` に出力されます。

生成されるファイル:

- `dist/django_deploy_probes-0.1.0.tar.gz`
- `dist/django_deploy_probes-0.1.0-py3-none-any.whl`

### インストールテスト

ビルド後、clean environment で wheel をインストールして確認します。

```bash
python -m venv /tmp/django-deploy-probes-install-test
source /tmp/django-deploy-probes-install-test/bin/activate
pip install dist/django_deploy_probes-0.1.0-py3-none-any.whl
python -c "import django_deploy_probes; print(django_deploy_probes.__version__)"
```

### PyPI への公開

GitHub Release を公開すると、`.github/workflows/publish.yml` が PyPI Trusted Publishing で公開します。

[英語 README に戻る](../README.md)
