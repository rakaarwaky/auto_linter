"""plugin_system — Entry point discovery and loading for custom adapters.

Allows third-party adapters to be discovered via Python entry points.

Usage in pyproject.toml of a plugin package:
    [project.entry-points."auto_linter.adapters"]
    my_custom_adapter = my_plugin:MyCustomAdapter

Then auto-linter will auto-discover it.
"""

from __future__ import annotations

import importlib.metadata
import logging
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)

# Registry of discovered custom adapters
_custom_adapters: Dict[str, Type] = {}


def discover_plugins(group: str = "auto_linter.adapters") -> Dict[str, Type]:
    """Discover custom adapters via entry points.

    Scans for entry points registered under the given group.

    Args:
        group: Entry point group name (default: "auto_linter.adapters")

    Returns:
        Dict mapping adapter name to adapter class.
    """
    discovered = {}

    try:
        eps = importlib.metadata.entry_points()
        # Python 3.10+ returns SelectableGroups, 3.9 returns dict
        if hasattr(eps, "select"):
            group_eps = list(eps.select(group=group))
        elif isinstance(eps, dict):
            group_eps = eps.get(group, [])
        else:
            group_eps = []

        for ep in group_eps:
            try:
                adapter_class = ep.load()
                discovered[ep.name] = adapter_class
                logger.info(f"Discovered plugin: {ep.name} -> {adapter_class}")
            except Exception as e:
                logger.warning(f"Failed to load plugin {ep.name}: {e}")
    except Exception as e:
        logger.warning(f"Entry point discovery failed: {e}")

    return discovered


def register_custom_adapter(name: str, adapter_class: Type) -> None:
    """Manually register a custom adapter.

    Args:
        name: Adapter name (e.g. "my_custom_linter")
        adapter_class: The adapter class to register.
    """
    _custom_adapters[name] = adapter_class
    logger.info(f"Manually registered adapter: {name}")


def unregister_custom_adapter(name: str) -> Optional[Type]:
    """Unregister a custom adapter.

    Args:
        name: Adapter name to unregister.

    Returns:
        The unregistered class, or None if not found.
    """
    return _custom_adapters.pop(name, None)


def get_custom_adapter(name: str) -> Optional[Type]:
    """Get a registered custom adapter by name.

    Args:
        name: Adapter name.

    Returns:
        The adapter class, or None if not found.
    """
    return _custom_adapters.get(name)


def list_custom_adapters() -> List[Dict[str, Any]]:
    """List all registered custom adapters.

    Returns:
        List of dicts with adapter info.
    """
    result = []
    for name, cls in _custom_adapters.items():
        result.append({
            "name": name,
            "class": f"{cls.__module__}.{cls.__name__}",
            "doc": cls.__doc__ or "",
        })
    return result


def load_all_plugins() -> Dict[str, Type]:
    """Discover and register all plugins from entry points.

    Returns:
        Dict of all discovered adapter classes.
    """
    discovered = discover_plugins()
    for name, cls in discovered.items():
        register_custom_adapter(name, cls)
    return _custom_adapters.copy()
