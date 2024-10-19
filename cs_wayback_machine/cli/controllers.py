from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Result:
    message: str
    exit_code: int = 0
