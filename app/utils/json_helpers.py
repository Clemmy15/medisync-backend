import json
from typing import Any


def safe_json_loads(data: str | None) -> dict[str, Any] | list[Any] | None:
    if not data:
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


def safe_json_dumps(data: Any) -> str:
    return json.dumps(data, default=str)
