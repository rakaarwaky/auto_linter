"""JSTracer - Naming variants for JavaScript/TypeScript symbols."""
from __future__ import annotations
import re
from typing import List, cast


def get_variant_dict(name: str) -> dict:
    """Produce common naming variants for a symbol name."""
    words = re.findall(r"[A-Za-z][a-z0-9]*|[A-Z]+(?=[A-Z][a-z0-9]|\b)|[0-9]+", name)
    words = cast(List[str], [w.lower() for w in words])
    if not words:
        return {"snake_case": name, "camel_case": name, "pascal_case": name, "screaming_snake": name}
    snake_case = "_".join(words)
    first = str(words[0])
    rest = "".join(str(w).capitalize() for w in words[1:])
    return {
        "snake_case": snake_case,
        "camel_case": first + rest,
        "pascal_case": "".join(str(w).capitalize() for w in words),
        "screaming_snake": snake_case.upper(),
    }


def build_variants(name: str) -> List[str]:
    """Build list of naming variants (snake, camel, pascal, screaming, kebab)."""
    d = get_variant_dict(name)
    kebab = d["snake_case"].replace("_", "-")
    return list({name, d["snake_case"], d["camel_case"], d["pascal_case"], d["screaming_snake"], kebab})
