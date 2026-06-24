from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def sgt_now() -> str:
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat(timespec="seconds")
