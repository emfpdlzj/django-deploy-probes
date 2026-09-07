# django-deploy-probes

このドキュメントは [ドキュメントホーム](index.md) を基にした日本語クイックスタートです。

Django deployment probe endpoint を提供します。

## インストール

```bash
pip install django-deploy-probes
```

対応ランタイムは Python 3.10–3.14 と Django 5.2 LTS、6.0、6.1 です。Django 4.2 が必要な
プロジェクトでは `0.3.x` リリース系列を使用してください。

Redis、Celery、OpenAPI 連携は extras として必要に応じてインストールできます。Storage
check は Django の storage alias を再利用するため、追加の extra は不要です。

```bash
pip install "django-deploy-probes[redis]"
pip install "django-deploy-probes[celery]"
pip install "django-deploy-probes[openapi]"
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

Include 方式では `/healthz`、`/readyz`、`/startupz`、`/version` が提供されます。HTTP
endpoint と同じ payload contract を CLI からも利用できます。

```bash
python manage.py deploy_probes healthz --json
python manage.py deploy_probes readyz --json
python manage.py deploy_probes startupz --json
python manage.py deploy_probes version --json
```

Readiness および startup のカスタム check メッセージはデフォルトで非表示です。
`EXPOSE_CHECK_MESSAGES=True` を使う場合は、secret や機密情報をメッセージに含めないで
ください。

Security check はデフォルトで `REMOTE_ADDR` を使用します。Trusted reverse proxy の背後で probe にアクセスする場合は、`TRUSTED_PROXY_NETWORKS` と `CLIENT_IP_HEADER` を設定して元の client IP を安全に判定してください。

Storage check は local filesystem、S3-compatible backend、および Django `STORAGES` に登録した
custom backend を検査できます。詳細は [endpoint reference](api.md#storage-checks) を参照して
ください。

## ビルドと公開

### ビルド

```bash
uv build
```

生成された distribution は `dist/` に出力されます。

生成されるファイル:

- `dist/django_deploy_probes-0.6.1.tar.gz`
- `dist/django_deploy_probes-0.6.1-py3-none-any.whl`

### インストールテスト

ビルド後、clean environment で wheel をインストールして確認します。

```bash
python -m venv /tmp/django-deploy-probes-install-test
source /tmp/django-deploy-probes-install-test/bin/activate
pip install dist/django_deploy_probes-0.6.1-py3-none-any.whl
python -c "import django_deploy_probes; print(django_deploy_probes.__version__)"
```

### PyPI への公開

GitHub Release を公開すると、`.github/workflows/publish.yml` が PyPI Trusted Publishing で公開します。

[英語ドキュメントホームに戻る](index.md)
