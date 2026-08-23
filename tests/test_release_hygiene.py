from pathlib import Path

from django.test import SimpleTestCase

from django_deploy_probes import __version__

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ReleaseHygieneTestCase(SimpleTestCase):
    def test_changelog_starts_with_current_version(self):
        changelog = (REPOSITORY_ROOT / "CHANGELOG.md").read_text()
        headings = [line for line in changelog.splitlines() if line.startswith("## ")]

        self.assertTrue(headings)
        self.assertEqual(headings[0], f"## v{__version__}")

    def test_localized_release_docs_reference_current_artifacts(self):
        expected_tarball = f"dist/django_deploy_probes-{__version__}.tar.gz"
        expected_wheel = f"dist/django_deploy_probes-{__version__}-py3-none-any.whl"

        for relative_path in ("docs/ko.md", "docs/ja.md", "docs/zh-CN.md"):
            content = (REPOSITORY_ROOT / relative_path).read_text()

            self.assertIn(expected_tarball, content, relative_path)
            self.assertIn(expected_wheel, content, relative_path)
