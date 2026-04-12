"""Comprehensive tests for capabilities/hooks_management_actions.py — 100% coverage."""

import pytest
from unittest.mock import MagicMock
from capabilities.hooks_management_actions import HookManagementUseCase


class TestHookManagementUseCase:
    def test_install_default(self):
        mock_manager = MagicMock()
        mock_manager.install_pre_commit.return_value = True
        use_case = HookManagementUseCase(mock_manager)
        assert use_case.install() is True
        mock_manager.install_pre_commit.assert_called_once()

    def test_install_custom_executable(self):
        mock_manager = MagicMock()
        mock_manager.install_pre_commit.return_value = True
        use_case = HookManagementUseCase(mock_manager)
        assert use_case.install(executable="custom-lint") is True
        mock_manager.install_pre_commit.assert_called_once_with("custom-lint")

    def test_install_failure(self):
        mock_manager = MagicMock()
        mock_manager.install_pre_commit.return_value = False
        use_case = HookManagementUseCase(mock_manager)
        assert use_case.install() is False

    def test_uninstall_success(self):
        mock_manager = MagicMock()
        mock_manager.uninstall_pre_commit.return_value = True
        use_case = HookManagementUseCase(mock_manager)
        assert use_case.uninstall() is True
        mock_manager.uninstall_pre_commit.assert_called_once()

    def test_uninstall_failure(self):
        mock_manager = MagicMock()
        mock_manager.uninstall_pre_commit.return_value = False
        use_case = HookManagementUseCase(mock_manager)
        assert use_case.uninstall() is False
