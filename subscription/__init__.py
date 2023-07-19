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
from models import Subscription
from spider import get_spider
from spider.routes.base import BaseSpider

# debug输出
scheduler = AsyncIOScheduler()


def load_subscription()->List[Subscription]:
    """
    读取订阅文件，将订阅加入执行队列
    """
    
    # todo: 读取订阅文件, Action配置怎么根据json转换成对应的类？
    # 下面都是测试代码
    t = TelegramAction()
    t.dynamic_config.chat_ids = [1071840459]

    actions=[BaseAction(),t]
    # 写入json
    with open("actions.json","w",encoding="utf-8") as f:
        import json
        f.write(json.dumps(actions,default=lambda obj:obj.__dict__,indent=4,ensure_ascii=False))
    
    # 读取json
    with open("actions.json","r",encoding="utf-8") as f:
        import json
        actions = json.loads(f.read())
        actions = create_actions(actions)
        logger.info(f"读取到的 actions: {actions}")

    return [Subscription(name="测试",url="https://baidu.com",cron="*/5 * * * * *",spider_name="RssSpider",actions=actions)]


def create_trigger(subscription:Subscription)->Optional[CronTrigger]:
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


async def check_subscription(subscription:Subscription,spider:BaseSpider):
    """
    检查订阅是否更新
    """
    logger.info(f"检查订阅: {subscription.name}")
    adatas = await spider.start(subscription)
    if adatas:
        # todo: 保存数据、去重复

        
        tasks = []
        for action in subscription.actions:
            if action.name in spider.support_actions:
                tasks.append(action.execute(adatas,subscription))
        asyncio.gather(*tasks)


def add_job(subscription:Subscription):
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
    scheduler.add_job(check_subscription, trigger=trigger, args=(subscription,spider), id=subscription.name, misfire_grace_time=3,next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=1))
    logger.info(f"定时任务添加成功: {subscription.name}")

def add_jobs(subscriptions:List[Subscription]):
    """
    添加任务
    """
    for subscription in subscriptions:
        add_job(subscription)

def remove_job(subscription:Subscription):
    """
    移除任务
    """
    scheduler.remove_job(subscription.name)


async def start_subscription():
    scheduler.start()
    subs = load_subscription()
    add_jobs(subs)
    logger.info(f"当前任务数量: {len(scheduler.get_jobs())}")
    # scheduler.print_jobs()