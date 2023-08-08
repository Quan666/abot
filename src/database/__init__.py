"""
数据库模块
去重复、数据存储
"""


from typing import Any, Dict, List
from src.action import create_actions
from src.models import AData, Subscription
from config import config
import json
import aiofiles


import os
from src.spider import create_spider


from src.subscription.scheduler import (
    add_sub_async_decorator,
    update_job_async_decorator,
    remove_job_async_decorator,
)

# 判断数据存储位置是否存在
if not os.path.exists(config.data_path):
    os.makedirs(config.data_path)

# 保存订阅配置的路径
subscription_path = f"{config.data_path}/config"

if not os.path.exists(subscription_path):
    os.makedirs(subscription_path)


async def save_subscriptions(subscriptions: List[Subscription]):
    """
    保存订阅配置
    """
    async with aiofiles.open(
        f"{subscription_path}/config.json", "w", encoding="utf-8"
    ) as f:
        datas = []
        for subscription in subscriptions:
            # 将对象转换为 json
            data = subscription.model_dump()
            # 去掉 spider 和 actions 的 static_config 字段
            del data["spider"]["static_config"]
            for action in data["actions"]:
                del action["static_config"]
            datas.append(data)
        await f.write(
            json.dumps(
                datas,
                indent=4,
                ensure_ascii=False,
            )
        )


async def load_subscriptions() -> List[Subscription]:
    """
    读取订阅配置
    """
    result = []
    try:
        async with aiofiles.open(
            f"{subscription_path}/config.json", "r", encoding="utf-8"
        ) as f:
            subscriptions = json.loads(await f.read())
            for subscription in subscriptions:
                subscription["spider"] = create_spider(subscription["spider"])
                subscription["actions"] = create_actions(
                    subscription.get("actions", [])
                )

                result.append(Subscription(**subscription))
            return result
    except Exception:
        return []


@add_sub_async_decorator
async def add_subscription(subscription: Subscription):
    """
    添加订阅
    """
    subscriptions = await load_subscriptions()
    subscriptions.append(subscription)
    await save_subscriptions(subscriptions)


@update_job_async_decorator
async def update_subscription(
    old_subscription: Subscription, subscription: Subscription
):
    """
    更新订阅
    """
    subscriptions = await load_subscriptions()
    for index, sub in enumerate(subscriptions):
        if sub.name == old_subscription.name:
            subscriptions[index] = subscription
            break
    await save_subscriptions(subscriptions)


@remove_job_async_decorator
async def delete_subscription(subscription: Subscription):
    """
    删除订阅
    """
    subscriptions = await load_subscriptions()
    for index, sub in enumerate(subscriptions):
        if sub.name == subscription.name:
            subscriptions.pop(index)
            break
    await save_subscriptions(subscriptions)
