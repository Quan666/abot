"""
行为模块
每个行为模块都是一个类，继承自Action类
包含触发条件、执行动作、配置信息（包括固定配置，和动态配置，动态配置为订阅时配置，如触发条件）
"""

import os
from typing import List


ACTIONS = {}

ACTIONS_FUN_LIST = {}

# 扫描action目录，将所有action存入ACTIONS，key为模块__ACTION_NAME__字段，value为action类
for file in os.listdir(os.path.dirname(__file__)):
    if file == "__init__.py" or not file.endswith(".py"):
        continue
    module_name = file[:-3]
    # 获取模块中所有的类
    module = __import__(f"src.action.{module_name}", fromlist=[module_name])
    # 加载结尾为Action的类
    for attr in dir(module):
        if attr.endswith("Action"):
            action = getattr(module, attr)
            ACTIONS[module.__ACTION_NAME__] = action
            ACTIONS_FUN_LIST[module.__ACTION_NAME__] = module.__FUNC_LIST__


def create_actions(data: List[dict]):
    """
    根据json配置, 创建action实例
    """
    actions = []
    for d in data:
        action = ACTIONS[d["name"]](**d)
        action.static_config = action.static_config.__class__()
        actions.append(action)
    return actions
