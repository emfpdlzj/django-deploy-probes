from pathlib import Path

from django.test import SimpleTestCase

from django_deploy_probes import __version__

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ReleaseHygieneTestCase(SimpleTestCase):
    @property
    def release_line(self):
        major, minor, _patch = __version__.split(".")
        return f"{major}.{minor}.x"

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

    def test_support_policy_references_current_release_line(self):
        support = (REPOSITORY_ROOT / "SUPPORT.md").read_text()

        self.assertIn(f"current `{self.release_line}` release line", support)

    def test_security_policy_marks_current_release_line_as_supported(self):
        security = (REPOSITORY_ROOT / "SECURITY.md").read_text()
        version_range = "3.10\N{EN DASH}3.14"
        expected_row = f"| {self.release_line} | {version_range} | 5.2 LTS, 6.0, 6.1 | Supported |"

        self.assertIn(expected_row, security)
