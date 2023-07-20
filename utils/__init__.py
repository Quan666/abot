from typing import Optional
import arrow
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

def get_timestamp() -> int:
    """
    获取当前时间戳, 13 位
    """
    return int(arrow.now().float_timestamp * 1000)



def create_trigger(cron:str) -> Optional[CronTrigger]:
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