"""Agent pipeline — receive→think→act→respond orchestrator."""

from __future__ import annotations
import logging
import asyncio
from typing import Any, List

from agent.tracking_job_registry import create_job, complete_job, fail_job, run_with_retry

logger = logging.getLogger("agent.pipeline")


class Pipeline:
    """Orchestrates request → thinking → action → response.

    The brain stem of the agent:
    1. Receive — validate input, create job
    2. Think — decide which action to take
    3. Act — execute via capabilities/infrastructure
    4. Respond — format and return result
    """

    def __init__(self, container):
        self.container = container

    async def execute(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        use_retry: bool = False,
    ) -> dict[str, Any]:
        """Full pipeline execution: receive → think → act → respond."""
        # 1. Receive — create job
        job_id = await create_job(action)

        try:
            # 2. Think — validate and decide
            if not self._validate_action(action):
                return self._error_response(
                    f"Invalid action '{action}'", job_id=job_id,
                    suggestion="Use list_commands() for catalog",
                )

            # 3. Act — execute
            if use_retry:
                result = await run_with_retry(
                    lambda: self._dispatch(action, args or {}),
                )
            else:
                result = await self._dispatch(action, args or {})

            # 4. Respond — format and complete
            await complete_job(job_id, result)
            result["job_id"] = job_id
            return result

        except Exception as e:
            await fail_job(job_id, str(e))
            return self._error_response(str(e), job_id=job_id)

    async def execute_check(self, path: str) -> dict[str, Any]:
        """Direct lint check — optimized pipeline path."""
        job_id = await create_job("check")
        try:
            report = await self.container.analysis_use_case.execute(path)
            data = self.container.analysis_use_case.to_dict(report)
            await complete_job(job_id, data)
            data["job_id"] = job_id
            return data
        except Exception as e:
            await fail_job(job_id, str(e))
            return {"error": str(e), "job_id": job_id}

    async def _dispatch(self, action: str, args: dict) -> dict[str, Any]:
        """Dispatch action to the appropriate use case or tool."""
        if action in ("check", "scan"):
            path = args.get("path", ".")
            report = await self.container.analysis_use_case.execute(path)
            return self.container.analysis_use_case.to_dict(report)

        if action == "fix":
            path = args.get("path", ".")
            output = await self.container.fixes_use_case.execute(path)
            return {"output": output}

        if action == "security":
            path = args.get("path", ".")
            report = await self.container.analysis_use_case.execute(path)
            data = self.container.analysis_use_case.to_dict(report)
            return {"bandit": data.get("bandit", [])}

        if action == "complexity":
            path = args.get("path", ".")
            report = await self.container.analysis_use_case.execute(path)
            data = self.container.analysis_use_case.to_dict(report)
            return {"radon": data.get("radon", [])}

        if action == "duplicates":
            path = args.get("path", ".")
            report = await self.container.analysis_use_case.execute(path)
            data = self.container.analysis_use_case.to_dict(report)
            return {"duplicates": data.get("duplicates", [])}

        if action == "trends":
            path = args.get("path", ".")
            report = await self.container.analysis_use_case.execute(path)
            data = self.container.analysis_use_case.to_dict(report)
            return {"trends": data.get("trends", [])}

        if action == "report":
            path = args.get("path", ".")
            output_format = args.get("format", "text")
            report = await self.container.analysis_use_case.execute(path)
            data = self.container.analysis_use_case.to_dict(report)

            if output_format == "json":
                return {"format": "json", "data": data}
            if output_format == "sarif":
                from capabilities.linting_report_formatters import to_sarif
                return {"format": "sarif", "data": to_sarif(data)}
            if output_format == "junit":
                from capabilities.linting_report_formatters import to_junit
                return {"format": "junit", "data": to_junit(data)}
            return {"format": "text", "data": data}

        if action == "version":
            from importlib.metadata import version as _v, PackageNotFoundError
            try:
                ver = _v("auto-linter")
            except PackageNotFoundError:
                ver = "1.0.0"
            return {"version": ver}

        if action == "adapters":
            return {"adapters": [a.name() for a in self.container.adapters]}

        if action in ("install-hook", "install_hook"):
            ok = self.container.hooks_use_case.install()
            return {"installed": ok}

        if action in ("uninstall-hook", "uninstall_hook"):
            ok = self.container.hooks_use_case.uninstall()
            return {"uninstalled": ok}

        return {"error": f"No pipeline handler for action: {action}"}

    def _validate_action(self, action: str) -> bool:
        """Check if action is known."""
        valid = {
            "check", "scan", "fix", "report", "security",
            "complexity", "duplicates", "trends",
            "version", "adapters", "install-hook", "install_hook",
            "uninstall-hook", "uninstall_hook",
        }
        return action in valid

    @staticmethod
    def _error_response(msg: str, **extra) -> dict:
        response = {"error": msg}
        response.update(extra)
        return response

    # === MULTI-PROJECT ORCHESTRATION ===

    async def execute_multi_project(
        self,
        paths: List[str],
        use_retry: bool = False,
    ) -> dict[str, Any]:
        """Orchestrate linting across multiple projects.
        
        This consolidates multi-project orchestration that was scattered in infrastructure.
        """
        job_id = await create_job("multi_project")

        try:
            # Create tasks for each project
            tasks = [self._lint_single_project(path) for path in paths]
            
            # Execute concurrently with asyncio.gather
            if use_retry:
                results = await asyncio.gather(
                    *[
                        run_with_retry(lambda p=path: self._lint_single_project(p))
                        for path in paths
                    ]
                )
            else:
                results = await asyncio.gather(*tasks)

            # Aggregate results
            aggregate = self._aggregate_multi_project_results(paths, results)
            await complete_job(job_id, aggregate)
            aggregate["job_id"] = job_id
            return aggregate

        except Exception as e:
            await fail_job(job_id, str(e))
            return self._error_response(str(e), job_id=job_id)

    async def _lint_single_project(self, path: str) -> dict[str, Any]:
        """Lint a single project and return result."""
        try:
            report = await self.container.analysis_use_case.execute(path)
            data = self.container.analysis_use_case.to_dict(report)
            return {
                "path": path,
                "score": data.get("score", 0.0),
                "is_passing": data.get("is_passing", False),
                "results": data,
            }
        except Exception as e:
            return {
                "path": path,
                "score": 0.0,
                "is_passing": False,
                "error": str(e),
            }

    def _aggregate_multi_project_results(
        self,
        paths: List[str],
        results: List[dict],
    ) -> dict[str, Any]:
        """Aggregate results from multiple projects."""
        total = len(results)
        passing = sum(1 for r in results if r.get("is_passing", False) and "error" not in r)
        failing = total - passing
        scores = [r.get("score", 0.0) for r in results if r.get("score", 0.0) > 0]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        return {
            "average_score": round(avg_score, 1),
            "all_passing": passing == total,
            "total_projects": total,
            "passing": passing,
            "failing": failing,
            "projects": results,
        }

    # === WATCH ORCHESTRATION ===


    async def execute_watch(self, path: str) -> dict[str, Any]:
        """Orchestrate watching a directory for changes and re-linting.
        
        This consolidates watch orchestration that was scattered in surfaces.
        Returns the initial lint result. The caller should set up the file watcher.
        """
        job_id = await create_job("watch")

        try:
            report = await self.container.analysis_use_case.execute(path)
            data = self.container.analysis_use_case.to_dict(report)
            await complete_job(job_id, data)
            data["job_id"] = job_id
            return data

        except Exception as e:
            await fail_job(job_id, str(e))
            return self._error_response(str(e), job_id=job_id)

    def process_watch_event(self, file_path: str) -> dict[str, Any]:
        """Process a file change event in watch mode.
        
        This is a sync method for use in watchdog event handlers.
        Safely handles async execution from both threaded and loop-running contexts.
        """
        async def _run_analysis():
            report = await self.container.analysis_use_case.execute(file_path)
            return self.container.analysis_use_case.to_dict(report)

        try:
            try:
                # Check if an event loop is already running in this thread
                loop = asyncio.get_running_loop()
                # If running, we are likely in an async context already.
                # Since this is a sync wrapper, we use run_coroutine_threadsafe if in a thread,
                # but this is tricky. For watchdog, it's usually a dedicated thread.
                fut = asyncio.run_coroutine_threadsafe(_run_analysis(), loop)
                data = fut.result(timeout=300)
            except RuntimeError:
                # No event loop in this thread (typical for watchdog threads)
                # It is safe to use asyncio.run()
                data = asyncio.run(_run_analysis())

            return {
                "file": file_path,
                "score": data.get("score", 0.0),
                "is_passing": data.get("is_passing", False),
                "results": data
            }
        except Exception as e:
            logger.error(f"Error processing watch event for {file_path}: {e}")
            return {
                "file": file_path,
                "error": str(e),
            }
