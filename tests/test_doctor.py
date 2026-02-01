"""Tests for doctor command utilities."""

import sys


class TestDoctorHelpers:
    """Test doctor command helper functions."""

    def test_check_mark_ok(self):
        from yami.cli.doctor import _check_mark

        result = _check_mark(True)
        assert "✓" in result
        assert "green" in result

    def test_check_mark_fail(self):
        from yami.cli.doctor import _check_mark

        result = _check_mark(False)
        assert "✗" in result
        assert "red" in result

    def test_warn_mark(self):
        from yami.cli.doctor import _warn_mark

        result = _warn_mark()
        assert "!" in result
        assert "yellow" in result


class TestVersionChecks:
    """Test version checking functionality."""

    def test_python_version_check(self):
        """Python version should be 3.10+."""
        assert sys.version_info >= (3, 10)

    def test_pymilvus_importable(self):
        """pymilvus should be importable."""
        import pymilvus

        assert hasattr(pymilvus, "__version__")

    def test_yami_version_available(self):
        """yami version should be available."""
        from yami.version import __version__

        assert __version__
        # Should be semver format
        parts = __version__.split(".")
        assert len(parts) >= 2
