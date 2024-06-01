"""
订阅处理
读取订阅文件，将订阅加入执行队列
"""

import asyncio
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import List, Optional

from loguru import logger
from src.models import Subscription
from config import config
from src.subscription.check import check_subscription
from src.utils import create_trigger
import functools
import inspect


# debug输出
scheduler = AsyncIOScheduler()


def add_job(subscription: Subscription):
    """
    添加任务
    """

    # 通过 cron 表达式添加任务
    trigger = create_trigger(subscription.cron)
    if trigger is None:
        logger.error(f"cron表达式错误: {subscription}")
        return
    scheduler.add_job(
        check_subscription,
        trigger=trigger,
        args=(subscription,),
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
            logger.debug(f"添加任务: {subscription.name}")


def remove_job(subscription: Subscription):
    """
    移除任务
    """
    try:
        # 先判断任务是否存在
        if scheduler.get_job(subscription.name):
            scheduler.remove_job(subscription.name)
            logger.debug(f"移除任务: {subscription.name}")
    except Exception as e:
        logger.error(f"移除任务失败: {subscription.name}, {e}")


def add_sub_async_decorator(func):
    """
    添加任务装饰器
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # 在这里获取被装饰函数的参数
        params = inspect.signature(func).bind(*args, **kwargs).arguments
        # 添加任务
        add_job(params["subscription"])
        # 执行被装饰函数
        result = await func(*args, **kwargs)

        return result

    return wrapper


def update_job_async_decorator(func):
    """
    更新任务装饰器
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # 在这里获取被装饰函数的参数
        params = inspect.signature(func).bind(*args, **kwargs).arguments
        # 移除任务
        remove_job(params["old_subscription"])

        subscription = params["subscription"]

        if subscription.enable:
            add_job(subscription)

        # 执行被装饰函数
        result = await func(*args, **kwargs)

        return result

    return wrapper


def remove_job_async_decorator(func):
    """
    删除任务装饰器
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # 在这里获取被装饰函数的参数
        params = inspect.signature(func).bind(*args, **kwargs).arguments
        # 移除任务
        remove_job(params["subscription"])
        # 执行被装饰函数
        result = await func(*args, **kwargs)

        return result

    return wrapper


async def start_scheduler(subs: List[Subscription]):
    scheduler.start()
    add_jobs(subs)
    logger.info(f"当前任务数量: {len(scheduler.get_jobs())}")
