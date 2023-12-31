import re
import importlib
import pkgutil
from typing import Any, List, Optional

from src.models import Subscription
from loguru import logger

from src.action import ACTIONS_FUN_LIST

SPIDES = []
ADATA_CLASS = {}


def register_spider(spider_cls):
    # 去重复
    for spider in SPIDES:
        if spider_cls.name == spider.name:
            return

    logger.debug(
        f"Spider: {spider_cls.name}, support_actions: {spider_cls.support_actions}"
    )
    SPIDES.append(spider_cls)


def get_spider_support_actions_by_name(name: str) -> List[str]:
    for spider in SPIDES:
        if name == spider.name:
            return spider.support_actions
    return []


# 匹配的spider
def match_spider(url: str) -> Optional[List[Any]]:
    result = []
    for spider in SPIDES:
        if re.search(spider.url_pattern, url):
            result.append(spider)
    return result


def get_all_spider() -> List[Any]:
    return SPIDES


# 扫描 routes下所有模块，Spider结尾的类都会被注册


def load_spider(path, parent_name):
    for importer, modname, ispkg in pkgutil.iter_modules(path):
        # 如果是子模块，递归读取子模块下的所有类
        if ispkg:
            sub_module = importlib.import_module(f"{parent_name}.{modname}")
            load_spider(sub_module.__path__, f"{parent_name}.{modname}")
            continue

        # 读取模块中的所有类
        module = importlib.import_module(f"{parent_name}.{modname}")
        # 读取 AData 结尾的类的所有方法
        func_list = []
        for attr in dir(module):
            if attr.endswith("AData"):
                # 获取类的所有方法
                func_list = [
                    func
                    for func in dir(getattr(module, attr))
                    if not func.startswith("__")
                ]
                # 保存类
                ADATA_CLASS[attr] = getattr(module, attr)

        for attr in dir(module):
            if attr.endswith("Spider"):
                spider = getattr(module, attr)

                # 根据实现的方法生成对应支持的Action
                support_actions = []
                for action_name, action_func_list in ACTIONS_FUN_LIST.items():
                    # 如果Spider实现了Action的所有方法，则支持该Action
                    if set(action_func_list).issubset(set(func_list)):
                        support_actions.append(action_name)
                register_spider(spider(support_actions=support_actions))


def create_spider(data: dict):
    """
    根据json配置, 创建 spider 实例
    """
    for spider in SPIDES:
        if data["name"] == spider.name:
            spider_data = spider.__class__(**data)
            spider_data.static_config = spider.static_config.__class__()
            return spider_data


# 扫描 routes下所有模块，Spider结尾的类都会被注册
import src.spider.routes as routes

load_spider(routes.__path__, "src.spider.routes")
