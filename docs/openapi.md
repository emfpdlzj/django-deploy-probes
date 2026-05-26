# OpenAPI Integration

Probe endpoints are not added to Swagger/OpenAPI documentation by default.

They are operational endpoints and should normally stay internal or be protected with the package security options documented in [Security options](security.md).

## Install

Install the OpenAPI extra:

```bash
pip install "django-deploy-probes[openapi]"
```

## Configure drf-spectacular

Enable probe documentation explicitly in `settings.py`:

```python
INSTALLED_APPS = [
    "django_deploy_probes",
    "rest_framework",
    "drf_spectacular",
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

DEPLOY_PROBES = {
    "ENABLE_OPENAPI": True,
    "OPENAPI_TAG": "Deployment Probes",
}
```

Add drf-spectacular schema and Swagger UI URLs in your project `urls.py`:

```python
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", include("django_deploy_probes.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
```

## Behavior

If `ENABLE_OPENAPI=True` but drf-spectacular is not installed, the probe views continue to work without schema metadata.

`drf-yasg` is not implemented in this phase and is reserved for future compatibility work.

## Security

Do not expose operational probe documentation publicly without reviewing the response shape and security settings.

Pay special attention to:

- `DETAIL_LEVEL`
- `EXPOSE_CHECK_MESSAGES`
- `EXPOSE_BUILD_INFO`
- `INTERNAL_IP_ONLY`
- `HEADER_TOKEN_VALIDATION`
