"""
行为模块
每个行为模块都是一个类，继承自Action类
包含触发条件、执行动作、配置信息（包括固定配置，和动态配置，动态配置为订阅时配置，如触发条件）
"""

from typing import List, Optional
from pydantic import BaseModel
from loguru import logger
from config import ConfigEnv, env_config
from src.models import AData, Subscription

from telethon import TelegramClient, events
from pydantic_settings import BaseSettings, SettingsConfigDict


__ACTION_NAME__ = "BaseAction"
__FUNC_LIST__: Optional[List[str]] = []
"""
Action 需要支持的方法列表
"""


class BaseActionStaticConfig(BaseSettings):
    """
    静态配置
    """

    model_config = SettingsConfigDict(
        env_file=f".env.{env_config.env}",
        env_file_encoding="utf-8",
        env_prefix="BASE_ACTION_",
        extra="allow",
    )

    log_prefix: Optional[str] = "BaseAction: "


class BaseActionDynamicConfig(BaseModel):
    """
    动态配置
    """

    async def telegram_setting(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
    ) -> None:
        """
        动态配置, Telegram 交互设置, 继承此类需要重写
        """
        pass

    async def telegram_text(self):
        """
        Telegram 配置展示文本, 继承此类 可以选择
        """
        tmp = "\n".join([f"  - {k}: {v}" for k, v in self.model_dump().items()])
        return f"{tmp if tmp.strip() else '  无'}"


class BaseAction(BaseModel):
    """
    Action基类, 所有Action都需要继承此类并重写 name, description, execute 方法
    """

    name: Optional[str] = __ACTION_NAME__
    """
    行为名称
    """

    description: Optional[str] = "日志输出"
    """
    行为描述
    """

    static_config: Optional[BaseActionStaticConfig] = BaseActionStaticConfig()
    """
    静态配置
    """

    dynamic_config: Optional[BaseActionDynamicConfig] = BaseActionDynamicConfig()
    """
    动态配置
    """

    async def execute(self, datas: List[AData], subscription: Subscription) -> None:
        """
        执行
        """
        logger.info(f"{self.static_config.log_prefix}{self.name} 执行")
