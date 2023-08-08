"""
订阅处理
读取订阅文件，将订阅加入执行队列
"""

from loguru import logger
from src.database import load_subscriptions
from config import config
from src.subscription.scheduler import start_scheduler


async def start_subscription():
    await start_scheduler(await load_subscriptions())
