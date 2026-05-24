import sys
import types
from unittest import mock

from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from django_deploy_probes.openapi import apply_openapi_metadata


def make_dummy_view():
    def dummy_view(request):
        return None

    return dummy_view


class OpenApiTestCase(SimpleTestCase):
    @override_settings(DEPLOY_PROBES={"ENABLE_OPENAPI": False})
    def test_openapi_disabled_keeps_existing_endpoint_behavior(self):
        response = self.client.get(reverse("django_deploy_probes:healthz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @override_settings(DEPLOY_PROBES={"ENABLE_OPENAPI": True})
    def test_missing_drf_spectacular_falls_back_without_import_error(self):
        dummy_view = make_dummy_view()

        original_import = __import__

        def raise_for_drf_spectacular(name, *args, **kwargs):
            if name == "drf_spectacular.utils":
                raise ImportError("drf-spectacular is not installed")
            return original_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=raise_for_drf_spectacular):
            decorated = apply_openapi_metadata("healthz", dummy_view)

        self.assertIs(decorated, dummy_view)
        self.assertFalse(hasattr(decorated, "_deploy_probes_openapi"))

    @override_settings(
        DEPLOY_PROBES={
            "ENABLE_OPENAPI": True,
            "OPENAPI_TAG": "Deployment Probes",
        }
    )
    def test_installed_drf_spectacular_applies_schema_metadata(self):
        dummy_view = make_dummy_view()
        drf_spectacular = types.ModuleType("drf_spectacular")
        rest_framework = types.ModuleType("rest_framework")
        decorators = types.ModuleType("rest_framework.decorators")
        utils = types.ModuleType("drf_spectacular.utils")

        class OpenApiResponse:
            def __init__(self, response=None, description=""):
                self.response = response
                self.description = description

        def extend_schema(**kwargs):
            def decorator(view):
                view._spectacular_kwargs = kwargs
                return view

            return decorator

        def api_view(methods):
            def decorator(view):
                view._api_view_methods = methods
                return view

            return decorator

        rest_framework.decorators = decorators
        decorators.api_view = api_view
        utils.OpenApiResponse = OpenApiResponse
        utils.extend_schema = extend_schema

        original_package = sys.modules.get("drf_spectacular")
        original_utils = sys.modules.get("drf_spectacular.utils")
        original_rest_framework = sys.modules.get("rest_framework")
        original_decorators = sys.modules.get("rest_framework.decorators")
        sys.modules["drf_spectacular"] = drf_spectacular
        sys.modules["drf_spectacular.utils"] = utils
        sys.modules["rest_framework"] = rest_framework
        sys.modules["rest_framework.decorators"] = decorators
        try:
            decorated = apply_openapi_metadata("readyz", dummy_view)
        finally:
            if original_package is None:
                sys.modules.pop("drf_spectacular", None)
            else:
                sys.modules["drf_spectacular"] = original_package
            if original_utils is None:
                sys.modules.pop("drf_spectacular.utils", None)
            else:
                sys.modules["drf_spectacular.utils"] = original_utils
            if original_rest_framework is None:
                sys.modules.pop("rest_framework", None)
            else:
                sys.modules["rest_framework"] = original_rest_framework
            if original_decorators is None:
                sys.modules.pop("rest_framework.decorators", None)
            else:
                sys.modules["rest_framework.decorators"] = original_decorators

        self.assertIs(decorated, dummy_view)
        self.assertEqual(decorated._api_view_methods, ["GET"])
        self.assertEqual(decorated._spectacular_kwargs["tags"], ["Deployment Probes"])
        self.assertEqual(decorated._spectacular_kwargs["summary"], "Readiness probe")
        self.assertIn(200, decorated._spectacular_kwargs["responses"])
        self.assertIn(503, decorated._spectacular_kwargs["responses"])
