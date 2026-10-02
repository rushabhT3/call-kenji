"""Wall-clock time, always timezone-aware."""

from datetime import datetime


class SystemClock:
    def now(self) -> datetime:
        return datetime.now().astimezone()
