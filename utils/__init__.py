import math
from typing import Optional
import arrow
from apscheduler.triggers.cron import CronTrigger
from loguru import logger


def get_timestamp() -> int:
    """
    获取当前时间戳, 13 位
    """
    return int(arrow.now().float_timestamp * 1000)


def timestamp2human(timestamp: int) -> str:
    """
    时间戳转换为人类可读时间
    """
    return arrow.get(timestamp).to("Asia/Shanghai").format("YYYY-MM-DD HH:mm:ss")


def create_trigger(cron: str) -> Optional[CronTrigger]:
    try:
        times_list = cron.split(" ")
        # 制作一个触发器
        trigger = CronTrigger(
            second=times_list[0],
            minute=times_list[1],
            hour=times_list[2],
            day=times_list[3],
            month=times_list[4],
            day_of_week=times_list[5],
            timezone="Asia/Shanghai",
        )
        return trigger
    except Exception:
        return None


def convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def get_quarter(timestamp: int) -> str:
    """
    根据时间戳获取季度 格式： YYYY-MM
    只用 1、4、7、10 月份
    """
    arrow_time = arrow.get(timestamp)
    quarter = (arrow_time.month - 1) // 3 + 1
    # 获取当前季度的第一个月
    first_month = (quarter - 1) * 3 + 1
    # 月份前面补0
    return f"{arrow_time.year}-{str(first_month).zfill(2)}"