"""SATYA_BASE_PATH override for student workspace resource resolution."""

import os
from unittest import mock

from system.utils.resource_path import get_base_path


def test_env_var_overrides_base_path(tmp_path):
    with mock.patch.dict(os.environ, {"SATYA_BASE_PATH": str(tmp_path)}):
        assert get_base_path() == tmp_path.resolve()


def test_without_env_var_falls_back_to_repo_root():
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop("SATYA_BASE_PATH", None)
        base = get_base_path()
        # Running from a checkout: package parent == repository root
        assert (base / "system" / "utils" / "resource_path.py").exists()


def test_env_var_beats_frozen_flag(tmp_path):
    with mock.patch.dict(os.environ, {"SATYA_BASE_PATH": str(tmp_path)}):
        with mock.patch("sys.frozen", True, create=True):
            assert get_base_path() == tmp_path.resolve()


def test_relative_env_var_resolved_absolute(tmp_path):
    with mock.patch.dict(os.environ, {"SATYA_BASE_PATH": "rel_base"}):
        base = get_base_path()
        assert base.is_absolute()
