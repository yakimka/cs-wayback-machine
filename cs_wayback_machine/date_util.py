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

    @property
    def days(self) -> int:
        return (self.end - self.start).days


def days_human_readable(days: int) -> str:
    if days <= 31:
        return f"{days} days"
    months = days // 31
    if months <= 11:
        return f"{months} months"
    years = months // 12
    months = months % 12
    if months:
        return f"{years} years, {months} months"
    return f"{years} years"
