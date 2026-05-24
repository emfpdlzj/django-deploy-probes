from unittest import mock

from django.test import SimpleTestCase
from django.urls import reverse


class HealthzTestCase(SimpleTestCase):
    def test_healthz_returns_ok(self):
        response = self.client.get(reverse("django_deploy_probes:healthz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_healthz_does_not_touch_external_dependencies(self):
        with (
            mock.patch("django.db.backends.utils.CursorWrapper.execute") as execute,
            mock.patch("django.core.cache.cache.get") as cache_get,
            mock.patch("django_deploy_probes.checks.registry.check_celery") as check_celery,
            mock.patch(
                "django_deploy_probes.checks.registry.check_custom_checks"
            ) as check_custom_checks,
            mock.patch("django_deploy_probes.checks.registry.check_migrations") as check_migrations,
            mock.patch("django_deploy_probes.checks.registry.check_redis") as check_redis,
        ):
            response = self.client.get(reverse("django_deploy_probes:healthz"))

        self.assertEqual(response.status_code, 200)
        execute.assert_not_called()
        cache_get.assert_not_called()
        check_celery.assert_not_called()
        check_custom_checks.assert_not_called()
        check_migrations.assert_not_called()
        check_redis.assert_not_called()
