"""
行为模块
每个行为模块都是一个类，继承自Action类
包含触发条件、执行动作、配置信息（包括固定配置，和动态配置，动态配置为订阅时配置，如触发条件）
"""

import asyncio
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger
from src.bot import get_bot
from src.bot.lib import InputListInt
from config import ConfigEnv, env_config
from src.models import AData, Subscription
from pikpakapi import PikPakApi
from telethon import TelegramClient, events
from pydantic_settings import BaseSettings, SettingsConfigDict
from config import config
from src.models.pikpak import PikPakDownloadInfo
from src.utils import convert_size, get_timestamp
from src.utils.cache import read_cache, write_cache

from .base import BaseAction, BaseActionStaticConfig, BaseActionDynamicConfig

__ACTION_NAME__ = "PikpakAction"
__FUNC_LIST__: Optional[List[str]] = ["pikpak_download"]
"""
Action 需要支持的方法列表
"""

PIKPAK_CACHE_KEY = "pikpak_login_info"

PIKPAK_CLIENT: Optional[PikPakApi] = None
PIKPAK_LAST_REFRESH_TOKEN_TIME: Optional[int] = None


class PikpakActionStaticConfig(BaseActionStaticConfig):
    """
    静态配置
    """

    model_config = SettingsConfigDict(
        env_file=f".env.{env_config.env}",
        env_file_encoding="utf-8",
        env_prefix="PIKPAK_ACTION_",
        extra="allow",
    )

    save_root_path: Optional[str] = "/My Pack"
    """
    保存路径
    """
    username: Optional[str] = None
    """
    用户名
    """
    password: Optional[str] = None
    """
    密码
    """


class PikpakActionDynamicConfig(BaseActionDynamicConfig):
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

    async def telegram_text(self):
        """
        Telegram 配置展示文本, 继承此类 可以选择
        """
        tmp = "\n".join([f"  - {k}: {v}" for k, v in self.dict().items()])
        return f"{tmp if tmp.strip() else '  无'}"


class PikpakAction(BaseAction):
    """
    Action基类, 所有Action都需要继承此类并重写 name, description, execute 方法
    """

    name: Optional[str] = __ACTION_NAME__
    """
    行为名称
    """

    description: Optional[str] = "PikPak离线"
    """
    行为描述
    """

    static_config: Optional[PikpakActionStaticConfig] = PikpakActionStaticConfig()
    """
    静态配置
    """

    dynamic_config: Optional[PikpakActionDynamicConfig] = PikpakActionDynamicConfig()
    """
    动态配置
    """

    async def execute(self, datas: List[AData], subscription: Subscription) -> None:
        """
        执行
        """
        messages = []
        for data in datas:
            info: PikPakDownloadInfo = await data.pikpak_download()
            if info:
                save_path = f"{self.static_config.save_root_path}/{info.save_path}"
                # 防止出现 // 的情况
                save_path = save_path.replace("//", "/")
                logger.debug(f"保存路径: {save_path}, 链接: {info.file_url}")
                try:
                    client = await self.get_pikpak_client()
                    # 先获取父文件夹
                    parent_folder = await client.path_to_id(save_path, create=True)
                    # 创建下载任务
                    res = await client.offline_download(
                        info.file_url, parent_folder[-1].get("id")
                    )
                    logger.debug(f"创建下载任务: {res}")
                    # 消息
                    messages.append(
                        f"<b>{data.title}</b>\n"
                        f"{convert_size(data.content_length)}\n"
                        f"<code>{info.file_url}</code>\n"
                        f"保存路径: {save_path}\n"
                    )
                except Exception as e:
                    if str(e) == "":
                        e = "请求超时"
                    messages.append(
                        f"<b>{data.title}</b>\n"
                        f"{convert_size(data.content_length)}\n"
                        f"<code>{info.file_url}</code>\n"
                        f"路径: {save_path}\n"
                        f"失败: {e}\n"
                    )
        tasks = []
        messages_str = f"<i>PikPak 离线</i>\n\n" + "\n----------\n".join(messages)
        for chat_id in self.dynamic_config.chat_ids:

            tasks.append(
                get_bot().send_message(
                    chat_id,
                    messages_str,
                    parse_mode="html",
                )
            )
        await asyncio.gather(*tasks)

    async def get_pikpak_client(self) -> PikPakApi:
        """
        获取 PikPak 实例, 从缓存中读取 token
        """
        global PIKPAK_CLIENT
        global PIKPAK_LAST_REFRESH_TOKEN_TIME
        if PIKPAK_CLIENT:
            # 60 分钟刷新一次 token
            if (
                PIKPAK_LAST_REFRESH_TOKEN_TIME
                and (PIKPAK_LAST_REFRESH_TOKEN_TIME + 60 * 60 * 1000) > get_timestamp()
            ):
                return PIKPAK_CLIENT
            try:
                await PIKPAK_CLIENT.refresh_access_token()
                PIKPAK_LAST_REFRESH_TOKEN_TIME = get_timestamp()
                return PIKPAK_CLIENT
            except Exception as e:
                logger.debug(f"PikPak refresh token 失败: {e}")

        try:
            PIKPAK_CLIENT = PikPakApi(
                username=self.static_config.username,
                password=self.static_config.password,
                proxy=config.proxy,
            )
            refresh_token = await read_cache(PIKPAK_CACHE_KEY)
            if refresh_token:
                PIKPAK_CLIENT.refresh_token = refresh_token
                try:
                    await PIKPAK_CLIENT.refresh_access_token()
                    return PIKPAK_CLIENT
                except Exception as e:
                    import traceback

                    traceback.print_exc()
                    logger.debug(f"PikPak refresh token 失败: {e}")

            await PIKPAK_CLIENT.login()
            return PIKPAK_CLIENT
        finally:
            if PIKPAK_CLIENT and PIKPAK_CLIENT.refresh_token:
                await write_cache(PIKPAK_CACHE_KEY, PIKPAK_CLIENT.refresh_token)
