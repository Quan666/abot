"""
数据库模块
去重复、数据存储
"""


from typing import Any, Dict, List
from action import create_actions
from models import AData, Subscription
from config import config
import json
import aiofiles

# 判断数据存储位置是否存在
import os

from spider import ADATA_CLASS

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
        await f.write(
            json.dumps(
                subscriptions,
                default=lambda obj: obj.__dict__,
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
                subscription["actions"] = create_actions(
                    subscription.get("actions", [])
                )
                result.append(Subscription(**subscription))
            return result
    except Exception:
        return []


async def save_adatas(adatas: List[AData], subscription: Subscription):
    """
    保存数据, 暂时存json
    """
    # 读取数据
    old_adatas = await load_adatas(subscription)
    # 合并数据
    adatas.extend(old_adatas)
    # 去重复
    adatas = list({adata.id: adata for adata in adatas}.values())

    async with aiofiles.open(
        f"{config.data_path}/{subscription.name}.json", "w", encoding="utf-8"
    ) as f:
        # 写入的时候，将对象转换为dict，并将对象类型写入 __type__ 字段
        json_data = []
        for adata in adatas:
            adata_dict = adata.__dict__
            adata_dict["__type__"] = adata.__class__.__name__
            json_data.append(adata_dict)
        await f.write(json.dumps(json_data, indent=4, ensure_ascii=False))


async def load_adatas(subscription: Subscription) -> List[AData]:
    """
    读取数据
    """
    result = []
    try:
        async with aiofiles.open(
            f"{config.data_path}/{subscription.name}.json", "r", encoding="utf-8"
        ) as f:
            adatas = json.loads(await f.read())
            for adata in adatas:
                adata_class = ADATA_CLASS.get(adata.get("__type__", None), AData)
                if adata_class:
                    result.append(adata_class(**adata))
            return result
    except Exception:
        return result


async def check_adatas(adatas: List[AData], subscription: Subscription) -> List[AData]:
    """
    检查数据是否重复
    """
    # 读取数据
    old_adatas = await load_adatas(subscription)
    old_id_set = set([old_adata.id for old_adata in old_adatas])
    # 去重复
    new_adatas = []
    for adata in adatas:
        if adata.id not in old_id_set:
            new_adatas.append(adata)
    return new_adatas
