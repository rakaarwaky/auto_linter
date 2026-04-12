from taxonomy.lint_result_models import IHookManager

class HookManagementUseCase:
    """Orchestrates git hook management (Capability)."""

    def __init__(self, manager: IHookManager):
        self.manager = manager

    def install(self, executable: str = "auto-lint") -> bool:
        return self.manager.install_pre_commit(executable)

    def uninstall(self) -> bool:
        return self.manager.uninstall_pre_commit()

