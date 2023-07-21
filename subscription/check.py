"""
订阅处理
读取订阅文件，将订阅加入执行队列
"""
import asyncio

from loguru import logger
from database.adata import save_adatas, check_adatas
from models import Subscription
from spider.routes.base import BaseSpider


async def check_subscription(subscription: Subscription, spider: BaseSpider):
    """
    检查订阅是否更新
    """
    logger.info(f"检查订阅: {subscription.name}")
    adatas = await spider.start(subscription)
    new_adatas = []
    if adatas:
        # todo: 保存数据、去重复
        new_adatas = await check_adatas(adatas, subscription)
    if new_adatas:

        tasks = []
        for action in subscription.actions:
            if action.name in spider.support_actions:
                tasks.append(action.execute(new_adatas, subscription))
        asyncio.gather(*tasks)

        await save_adatas(new_adatas, subscription)
