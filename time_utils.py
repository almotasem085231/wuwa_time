# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

def time_left_str(end_time: datetime, now: datetime) -> str:
    """
    Exact time calculation algorithm from wuwa.py
    """
    diff = end_time - now
    total_seconds = int(diff.total_seconds())
    if total_seconds <= 0:
        return "انتهى."
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    return f"{days} يوم و {hours} ساعة و {minutes} دقيقة و {seconds} ثانية"

def parse_end_datetime(date_time_str: str, offset_hours: int = 0) -> Optional[datetime]:
    """
    Exact parse datetime algorithm from wuwa.py
    Converts local server time into UTC.
    """
    try:
        tz = timezone(timedelta(hours=offset_hours))
        end_time = datetime.strptime(date_time_str.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
        return end_time.astimezone(timezone.utc)
    except Exception:
        return None

def format_countdown_data(end_time_utc_str: Optional[str]) -> Dict[str, Any]:
    """
    Takes a stored UTC time string ('%Y-%m-%d %H:%M:%S') and calculates
    remaining time, countdown breakdown, and ISO 8601 string for client timers.
    """
    if not end_time_utc_str:
        return {
            "raw": None,
            "iso_utc": None,
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "seconds": 0,
            "total_seconds": 0,
            "formatted": "غير محدد",
            "is_expired": True
        }
    
    now_utc = datetime.now(timezone.utc)
    try:
        end_time_utc = datetime.strptime(end_time_utc_str.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return {
            "raw": end_time_utc_str,
            "iso_utc": None,
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "seconds": 0,
            "total_seconds": 0,
            "formatted": "خطأ في التاريخ",
            "is_expired": True
        }
    
    diff = end_time_utc - now_utc
    total_seconds = int(diff.total_seconds())
    is_expired = total_seconds <= 0
    
    if is_expired:
        formatted = "انتهى."
        days = hours = minutes = seconds = 0
        rem_seconds = 0
    else:
        formatted = time_left_str(end_time_utc, now_utc)
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        rem_seconds = total_seconds

    # ISO 8601 with Z indicator
    iso_utc = end_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "raw": end_time_utc_str,
        "iso_utc": iso_utc,
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "total_seconds": rem_seconds,
        "formatted": formatted,
        "is_expired": is_expired
    }

