"""naming_analyzer — Naming variant generation capability."""

from __future__ import annotations
import re
from typing import List, cast
from taxonomy import SymbolName


def get_variant_dict(name: SymbolName | str) -> dict:
    """Produce common naming variants for a symbol name."""
    n = str(name) if isinstance(name, SymbolName) else name
    words = re.findall(r"[A-Za-z][a-z0-9]*|[A-Z]+(?=[A-Z][a-z0-9]|\b)|[0-9]+", n)
    words = cast(List[str], [w.lower() for w in words])
    if not words:
        return {"snake_case": n, "camel_case": n, "pascal_case": n, "screaming_snake": n}
    snake_case = "_".join(words)
    first = str(words[0])
    rest = "".join(str(w).capitalize() for w in words[1:])
    return {
        "snake_case": snake_case,
        "camel_case": first + rest,
        "pascal_case": "".join(str(w).capitalize() for w in words),
        "screaming_snake": snake_case.upper(),
    }


def build_variants(name: SymbolName | str) -> List[str]:
    """Build list of naming variants (snake, camel, pascal, screaming, kebab)."""
    n = str(name) if isinstance(name, SymbolName) else name
    d = get_variant_dict(n)
    kebab = d["snake_case"].replace("_", "-")
    return list({n, d["snake_case"], d["camel_case"], d["pascal_case"], d["screaming_snake"], kebab})
