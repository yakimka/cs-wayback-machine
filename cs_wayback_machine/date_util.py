from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class DateRange:
    start: date
    end: date

    @classmethod
    def create(cls, start: date, end: date | None = None) -> DateRange:
        return cls(start, end or datetime.now().date())

    def has_overlap(self, other: DateRange) -> bool:
        return self.start < other.end and self.end > other.start
