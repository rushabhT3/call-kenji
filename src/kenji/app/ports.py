"""Interfaces the application depends on; adapters implement them."""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...
