from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


# attempting new way of storing and processing data.
@dataclass
class TopoffRunResult:
    ok: bool
    status_code: int
    error: Optional[str] = None
    details: Optional[str] = None
    arduino_status_code: Optional[int] = None
    arduino_response: Optional[Any] = None
    seconds: Optional[float] = None
    final_status: Optional[dict[str, Any]] = None
