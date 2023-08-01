"""
订阅处理
读取订阅文件，将订阅加入执行队列
"""
import asyncio

from loguru import logger
from models import Subscription


async def check_subscription(subscription: Subscription):
    """
    检查订阅是否更新
    """
    logger.debug(f"检查订阅: {subscription.name}")
    new_adatas = await subscription.spider.start(subscription)
    if new_adatas:
        tasks = []
        for action in subscription.actions:
            if action.name in subscription.spider.support_actions:
                tasks.append(action.execute(new_adatas, subscription))
        asyncio.gather(*tasks)
