from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class DateRange:
    start: date
    end: date

    @classmethod
    def never(cls) -> DateRange:
        return cls(date.min, date.min)

    @classmethod
    def create(cls, start: date | None, end: date | None = None) -> DateRange:
        return cls(start or date.min, end or date.max)

    def has_overlap(self, other: DateRange) -> bool:
        return self.start < other.end and self.end > other.start
