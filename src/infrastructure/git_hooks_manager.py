import os
import stat
import logging

logger = logging.getLogger("mcp.infrastructure.git_hooks")

class GitHookManager:
  """Manages Git hooks for the project (Infrastructure)."""

  def __init__(self, root_dir: str):
    self.root_dir = root_dir
    self.git_dir = os.path.join(root_dir, ".git")

  def is_git_repo(self) -> bool:
    return os.path.exists(self.git_dir) and os.path.isdir(self.git_dir)

  def install_pre_commit(self, executable_path: str = "auto-lint") -> bool:
    if not self.is_git_repo():
      logger.error(f"Cannot install hook: {self.root_dir} is not a git repository.")
      return False

    hooks_dir = os.path.join(self.git_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    
    hook_path = os.path.join(hooks_dir, "pre-commit")
    
    hook_content = f"""#!/bin/bash
# Auto-Linter Pre-Commit Hook
echo " Running Auto-Linter check..."
{executable_path} check .
if [ $? -ne 0 ]; then
 echo " Linting failed. Please fix issues before committing."
 exit 1
fi
echo " Linting passed."
exit 0
"""
    try:
      with open(hook_path, "w") as f:
        f.write(hook_content)
      
      # Make the hook executable
      st = os.stat(hook_path)
      os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
      
      logger.info(f"Successfully installed pre-commit hook to {hook_path}")
      return True
    except Exception as e:
      logger.error(f"Failed to install pre-commit hook: {e}")
      return False

  def uninstall_pre_commit(self) -> bool:
    if not self.is_git_repo():
      return False
      
    hook_path = os.path.join(self.git_dir, "hooks", "pre-commit")
    if os.path.exists(hook_path):
      try:
        os.remove(hook_path)
        logger.info(f"Successfully removed pre-commit hook from {hook_path}")
        return True
      except Exception as e:
        logger.error(f"Failed to remove pre-commit hook: {e}")
        return False
    return True
