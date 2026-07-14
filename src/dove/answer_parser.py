from __future__ import annotations

import json
import re


def parse_answer(text: str, valid_options: list[str]) -> list[str]:
    """Parse option labels conservatively from JSON or common answer formats."""
    valid = {value.upper() for value in valid_options}
    try:
        data = json.loads(text.strip())
        value = data.get("answers", data.get("answer")) if isinstance(data, dict) else data
        values = value if isinstance(value, list) else [value]
        parsed = [str(item).upper() for item in values if str(item).upper() in valid]
        if parsed:
            return list(dict.fromkeys(parsed))
    except (json.JSONDecodeError, AttributeError):
        pass

    patterns = [
        r"(?i)(?:final\s+)?answers?\s*[:=-]\s*([A-Z](?:\s*[,;/&+]\s*[A-Z])*)",
        r"(?i)^\s*\[?\(?([A-Z](?:\s*[,;/&+]\s*[A-Z])*)\)?\]?\s*[.!]?\s*$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text.strip())
        if match:
            found = [x.upper() for x in re.findall(r"[A-Z]", match.group(1), re.I)]
            return list(dict.fromkeys(x for x in found if x in valid))
    return []

