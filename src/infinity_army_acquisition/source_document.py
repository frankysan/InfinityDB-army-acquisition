"""Source-document shape validation, without Army merging."""

from __future__ import annotations

import json
from typing import Any


def decode_document(raw: bytes, filename: str) -> dict[str, Any]:
    try:
        decoded = raw.decode("utf-8-sig")
        data = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not parse {filename}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{filename}: top-level JSON value is not an object")
    if not isinstance(data.get("units"), list):
        raise ValueError(f"{filename}: missing or invalid top-level 'units' array")
    return data
