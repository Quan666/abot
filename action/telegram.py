import asyncio
from typing import List, Optional

from pydantic_settings import SettingsConfigDict
from bot.lib import InputListInt
from config import ConfigEnv, env_config
from loguru import logger
from bot import get_bot
from models import AData, Subscription
from .base import BaseAction, BaseActionStaticConfig, BaseActionDynamicConfig
from telethon import TelegramClient, events

__ACTION_NAME__ = "TelegramAction"

__FUNC_LIST__: Optional[List[str]] = [
    "get_telegram_message_text",
    "get_telegram_message_config",
]
"""
Action 需要支持的方法列表
"""


class TelegramActionStaticConfig(BaseActionStaticConfig):
    """
    静态配置
    """

    model_config = SettingsConfigDict(
        env_file=f".env.{env_config.env}",
        env_file_encoding="utf-8",
        env_prefix="TELEGRAM_ACTION_",
        extra="allow",
    )


class TelegramActionDynamicConfig(BaseActionDynamicConfig):
    """
    动态配置
    """

    chat_ids: List[int] = []

    async def telegram_setting(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
    ) -> None:
        """
        动态配置, Telegram 交互设置
        """
        self.chat_ids = await InputListInt(
            bot,
            event,
            f"当前 Chat ID: `{event.chat_id}`\n输入需要推送的 Chat ID: ",
            self.chat_ids,
        ).input()


class TelegramAction(BaseAction):
    """
    TelegramAction
    """

    name: Optional[str] = __ACTION_NAME__
    """
    行为名称
    """

    description: Optional[str] = "Telegram 推送"
    """
    行为描述
    """

    static_config: Optional[TelegramActionStaticConfig] = TelegramActionStaticConfig()
    """
    静态配置
    """

    dynamic_config: Optional[
        TelegramActionDynamicConfig
    ] = TelegramActionDynamicConfig()
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

                telegram_config = await adata.get_telegram_message_config()
                tasks.append(
                    get_bot().send_message(
                        chat_id,
                        await adata.get_telegram_message_text(),
                        **telegram_config,
                    )
                )
        await asyncio.gather(*tasks)
