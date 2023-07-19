


import asyncio
from typing import List, Optional
from config import ConfigEnv
from loguru import logger
from bot import get_bot
from models import AData, Subscription
from .base import BaseAction,BaseActionStaticConfig,BaseActionDynamicConfig

__ACTION_NAME__ = "TelegramAction"

__FUNC_LIST__: Optional[List[str]] = ["get_telegram_message_text"]
"""
Action 需要支持的方法列表
"""


class TelegramActionStaticConfig(BaseActionStaticConfig):
    """
    静态配置
    """
    class Config(ConfigEnv):
        # 解析的前缀
        env_prefix = "TELEGRAM_ACTION_"

class TelegramActionDynamicConfig(BaseActionDynamicConfig):
    """
    动态配置
    """
    chat_ids: Optional[List[int]] = []

class TelegramAction(BaseAction):
    """
    TelegramAction
    """

    name: Optional[str]= __ACTION_NAME__
    """
    行为名称
    """

    description: Optional[str] = "向Telegram推送消息"
    """
    行为描述
    """



    static_config: Optional[TelegramActionStaticConfig] = TelegramActionStaticConfig()
    """
    静态配置
    """

    dynamic_config: Optional[TelegramActionDynamicConfig] = TelegramActionDynamicConfig()
    """
    动态配置
    """

    
    async def execute(self, data: List[AData], subscription: Subscription) -> None:
        """
        执行
        """
        tasks = []
        for chat_id in self.dynamic_config.chat_ids:
            for adata in data:
                tasks.append(get_bot().send_message(chat_id,adata.get_telegram_message_text()))
        await asyncio.gather(*tasks)
        
    
