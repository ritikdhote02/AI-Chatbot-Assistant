from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain.tools import tool


@tool
def get_current_datetime(timezone: str = "Asia/Kolkata") -> str:
    """
    Get the current date, time, day, and UTC offset for a timezone.

    Use an IANA timezone such as Asia/Kolkata, Europe/London,
    or America/New_York. Defaults to Asia/Kolkata.
    """
    try:
        selected_timezone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError, ValueError:
        return (
            f"Unable to retrieve the current time. "
            f"'{timezone}' is not a valid IANA timezone."
        )

    current_time = datetime.now(selected_timezone)

    return (
        f"Timezone: {timezone}\n"
        f"Date: {current_time.strftime('%A, %d %B %Y')}\n"
        f"Time: {current_time.strftime('%I:%M:%S %p')}\n"
        f"UTC offset: {current_time.strftime('%z')}\n"
        f"ISO timestamp: {current_time.isoformat()}"
    )
