"""Unified response envelope for Agent mode output."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ResponseMeta:
    """Metadata about the operation."""

    command: str | None = None
    duration_ms: int | None = None
    count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ErrorInfo:
    """Structured error information."""

    code: str
    message: str
    hint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ResponseEnvelope:
    """Unified response envelope for Agent mode.

    All responses use this format:
    - Success: {"ok": true, "data": <result>, "meta": {...}}
    - Error: {"ok": false, "error": {"code": "...", "message": "...", "hint": "..."}}
    """

    ok: bool
    data: Any = None
    error: ErrorInfo | None = None
    meta: ResponseMeta | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization."""
        result: dict[str, Any] = {"ok": self.ok}

        if self.ok:
            result["data"] = self.data
        else:
            if self.error:
                result["error"] = self.error.to_dict()

        if self.meta:
            meta_dict = self.meta.to_dict()
            if meta_dict:
                result["meta"] = meta_dict

        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str, ensure_ascii=False)


def success_envelope(
    data: Any,
    meta: ResponseMeta | None = None,
) -> ResponseEnvelope:
    """Create a success response envelope."""
    return ResponseEnvelope(ok=True, data=data, meta=meta)


def error_envelope(
    code: str,
    message: str,
    hint: str | None = None,
    meta: ResponseMeta | None = None,
) -> ResponseEnvelope:
    """Create an error response envelope."""
    return ResponseEnvelope(
        ok=False,
        error=ErrorInfo(code=code, message=message, hint=hint),
        meta=meta,
    )
