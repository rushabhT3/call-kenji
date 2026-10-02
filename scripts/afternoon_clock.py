"""A clock moved to 15:00 Japan time, for testing calls at any hour of the day."""

from datetime import datetime

from kenji.domain.calling_hours import JAPAN_STANDARD_TIME

AFTERNOON_HOUR = 15


class AfternoonInTokyoClock:
    """Real time, moved so the run starts at 15:00 Japan time today."""

    def __init__(self) -> None:
        real = datetime.now(JAPAN_STANDARD_TIME)
        self._offset = real.replace(hour=AFTERNOON_HOUR, minute=0, second=0, microsecond=0) - real

    def now(self) -> datetime:
        return datetime.now(JAPAN_STANDARD_TIME) + self._offset
