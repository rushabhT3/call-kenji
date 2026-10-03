"""A lender may only ring or visit a debtor between 08:00 and 21:00 Japan time.

Japan's Money Lending Business Act (art. 21) restricts contact the lender starts. It does not stop
Kenji answering a debtor who rings him, so the window governs outbound contact only.
"""

from datetime import datetime, time, timedelta, timezone

JAPAN_STANDARD_TIME = timezone(timedelta(hours=9), "JST")
CALLING_WINDOW_OPENS = time(8, 0)
CALLING_WINDOW_CLOSES = time(21, 0)


def to_japan_time(moment: datetime) -> datetime:
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("moment must be timezone-aware")
    return moment.astimezone(JAPAN_STANDARD_TIME)


def is_within_calling_hours(moment: datetime) -> bool:
    local_time = to_japan_time(moment).time()
    return CALLING_WINDOW_OPENS <= local_time < CALLING_WINDOW_CLOSES
