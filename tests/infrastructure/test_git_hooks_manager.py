"""Comprehensive tests for infrastructure/git_hooks_manager.py — 100% coverage."""

import os
import tempfile
import pytest
from infrastructure.git_hooks_manager import GitHookManager


class TestGitHookManager:
    def test_init_default(self):
        mgr = GitHookManager()
        assert mgr.root_dir == "."
        assert mgr.git_dir == os.path.join(".", ".git")

    def test_init_with_path(self):
        mgr = GitHookManager(root_dir="/tmp/test")
        assert mgr.root_dir == "/tmp/test"
        assert mgr.git_dir == "/tmp/test/.git"

    def test_is_not_git_repo(self):
        mgr = GitHookManager(root_dir="/tmp")
        assert not mgr.is_git_repo()

    def test_install_pre_commit_not_git(self):
        mgr = GitHookManager(root_dir="/tmp")
        assert mgr.install_pre_commit() is False

    def test_uninstall_pre_commit_not_git(self):
        mgr = GitHookManager(root_dir="/tmp")
        assert mgr.uninstall_pre_commit() is False

    def test_install_pre_commit_in_git_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = os.path.join(tmpdir, ".git")
            os.makedirs(git_dir)
            mgr = GitHookManager(root_dir=tmpdir)
            assert mgr.is_git_repo()
            assert mgr.install_pre_commit() is True
            hook_path = os.path.join(git_dir, "hooks", "pre-commit")
            assert os.path.exists(hook_path)
            # Check it's executable
            assert os.access(hook_path, os.X_OK)

    def test_install_pre_commit_custom_executable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = os.path.join(tmpdir, ".git")
            os.makedirs(git_dir)
            mgr = GitHookManager(root_dir=tmpdir)
            assert mgr.install_pre_commit(executable_path="custom-lint") is True
            hook_path = os.path.join(git_dir, "hooks", "pre-commit")
            content = open(hook_path).read()
            assert "custom-lint" in content

    def test_uninstall_pre_commit_in_git_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = os.path.join(tmpdir, ".git")
            os.makedirs(os.path.join(git_dir, "hooks"))
            mgr = GitHookManager(root_dir=tmpdir)
            # Install first
            mgr.install_pre_commit()
            assert mgr.uninstall_pre_commit() is True
            hook_path = os.path.join(git_dir, "hooks", "pre-commit")
            assert not os.path.exists(hook_path)

    def test_uninstall_pre_commit_no_hook(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = os.path.join(tmpdir, ".git")
            os.makedirs(os.path.join(git_dir, "hooks"))
            mgr = GitHookManager(root_dir=tmpdir)
            assert mgr.uninstall_pre_commit() is True  # No hook = already clean
