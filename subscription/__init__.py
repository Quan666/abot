"""
订阅处理
读取订阅文件，将订阅加入执行队列
"""
import asyncio
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import List, Optional

from loguru import logger
from action.base import BaseAction
from action.telegram import TelegramAction
from action import create_actions
from database import load_subscriptions, save_subscriptions,save_adatas,check_adatas
from models import Subscription
from spider import get_spider
from spider.routes.base import BaseSpider
from config import config

# debug输出
scheduler = AsyncIOScheduler()


async def load_subscription() -> List[Subscription]:
    """
    读取订阅文件，将订阅加入执行队列
    """
    return await load_subscriptions()


def create_trigger(subscription: Subscription) -> Optional[CronTrigger]:
    try:
        times_list = subscription.cron.split(" ")
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
        logger.exception(f"创建定时器错误, cron:{subscription.cron}")
        return None


async def check_subscription(subscription: Subscription, spider: BaseSpider):
    """
    检查订阅是否更新
    """
    logger.info(f"检查订阅: {subscription.name}")
    adatas = await spider.start(subscription)
    new_adatas = []
    if adatas:
        # todo: 保存数据、去重复
        new_adatas = await check_adatas(adatas,subscription)
    if new_adatas:
        

        tasks = []
        for action in subscription.actions:
            if action.name in spider.support_actions:
                tasks.append(action.execute(new_adatas, subscription))
        asyncio.gather(*tasks)

        await save_adatas(new_adatas, subscription)

def add_job(subscription: Subscription):
    """
    添加任务
    """
    spider = get_spider(subscription)
    if spider is None:
        logger.error(f"未找到对应的Spider: {subscription.spider_name}")
        return
    # 通过 cron 表达式添加任务
    trigger = create_trigger(subscription)
    if trigger is None:
        return
    scheduler.add_job(
        check_subscription,
        trigger=trigger,
        args=(subscription, spider),
        id=subscription.name,
        misfire_grace_time=3,
        next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=1),
    )
    logger.info(f"定时任务添加成功: {subscription.name}")


def add_jobs(subscriptions: List[Subscription]):
    """
    添加任务
    """
    for subscription in subscriptions:
        if subscription.enable:
            add_job(subscription)


def remove_job(subscription: Subscription):
    """
    移除任务
    """
    scheduler.remove_job(subscription.name)


async def start_subscription():
    scheduler.start()
    subs = await load_subscription()
    add_jobs(subs)
    logger.info(f"当前任务数量: {len(scheduler.get_jobs())}")
    # scheduler.print_jobs()
