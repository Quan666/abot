"""
Spider 部分
"""

import asyncio
import re
from typing import Callable, Optional, List
import arrow
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from telethon import TelegramClient, events
from src.bot import telegram_upload_file
from src.bot.inputs import url_input
from src.database.adata import check_adatas, save_adatas
from src.models import AData, Subscription
from src.utils import get_timestamp, timestamp2human
from src.utils.pic_download import pic_download
from src.utils.request import get, Response
from config import config, env_config
from loguru import logger


class BaseSpiderAData(AData):
    """
    Spider 数据模型 基类, 所有 Spider 数据模型都可以继承此类或者直接继承AData
    """

    pic_url: Optional[List[str]] = []

    pic_bytes: Optional[List[bytes]] = []

    async def download_pic_bytes(self) -> Optional[List[bytes]]:
        """
        下载图片
        """
        if self.pic_url and len(self.pic_bytes) != len(self.pic_url):
            tasks = []
            for url in self.pic_url:
                tasks.append(pic_download(url, proxy=config.proxy))
            self.pic_bytes = await asyncio.gather(*tasks)
        return self.pic_bytes

    async def get_telegram_message_text(self) -> str:
        """
        TelegramAction 的方法
        """
        text = f"<i>{self.source}</i>\n"
        text += f"{timestamp2human(self.push_time)}\n\n"
        text += f"{self.content}\n\n"
        text += f"<a href='{self.url}'>阅读原文</a>"
        return text

    async def get_telegram_message_config(self) -> dict:
        """
        TelegramAction 的方法, 发送消息时的配置
        """
        pics = await self.download_pic_bytes()
        media = []
        if pics:
            media = await telegram_upload_file(pics)
        # print(media)
        if media:
            return {
                "parse_mode": "html",
                "file": media,
            }
        else:
            return {
                "parse_mode": "html",
            }


class BaseSpiderStaticConfig(BaseSettings):
    """
    静态配置
    """

    model_config = SettingsConfigDict(
        env_file=f".env.{env_config.env}",
        env_file_encoding="utf-8",
        env_prefix="BASE_ACTION_",
        extra="allow",
    )


class BaseSpiderDynamicConfig(BaseModel):
    """
    动态配置
    """

    url: Optional[str] = None
    """
    url
    """

    async def telegram_setting(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
    ) -> None:
        """
        动态配置, Telegram 交互设置, 继承此类需要重写
        """
        text = ""
        if self.url:
            text += f"当前URL: `{self.url}`\n"
        text += "输入URL: "
        self.url = await url_input(bot, event, text)

    async def telegram_text(self):
        """
        Telegram 配置展示文本, 继承此类 可以选择
        """
        tmp = "\n".join([f"  - {k}: {v}" for k, v in self.model_dump().items()])
        return f"{tmp if tmp.strip() else '  无'}"


class BaseSpider(BaseModel):
    """
    Spider 模型
    """

    name: str = "BaseSpider"
    """
    Spider 名称
    """

    description: Optional[str] = "通用"
    """
    描述
    """

    url_pattern: str = ".*?"
    """
    url 匹配正则表达式
    """

    prefix: str = "BaseSpider"
    """
    唯一id 前缀
    """

    support_actions: List[str] = []
    """
    支持的Acton, 如果支持对应Acton, 必须实现对应的方法
    """

    static_config: Optional[BaseSpiderStaticConfig] = BaseSpiderStaticConfig()
    """
    静态配置
    """

    dynamic_config: Optional[BaseSpiderDynamicConfig] = BaseSpiderDynamicConfig()
    """
    动态配置
    """

    def get_only_id(self, id) -> Optional[str]:
        """
        获取唯一id,带前缀
        """
        return f"{self.prefix}_{id}"

    async def request(self, subscription: Subscription) -> Optional[Response]:
        """
        请求数据

        """
        proxy = None
        if subscription.enable_proxy:
            proxy = config.proxy
        try:
            return await get(subscription.spider.dynamic_config.url, proxy=proxy)
        except Exception as e:
            logger.error(f"Spider {self.name} request error: {e}")
            return None

    async def parse(
        self, subscription: Subscription, response: Response
    ) -> Optional[List[BaseSpiderAData]]:
        """
        解析数据
        """
        return [
            BaseSpiderAData(
                id=self.get_only_id(get_timestamp()),
                title=subscription.name,
                content=f"{response.content[:100]}...",
                url=subscription.spider.dynamic_config.url,
                source=subscription.name,
                push_time=get_timestamp(),
                extend={},
            )
        ]

    async def start(
        self, subscription: Subscription
    ) -> Optional[List[BaseSpiderAData]]:
        """
        开始流程
        """
        response = await self.request(subscription)
        if response:
            adatas = await self.parse(subscription, response)
            if adatas:
                new_adatas = await self.filter(adatas, subscription)
                new_adatas = await self.handle_new_adata(new_adatas, subscription)
                return new_adatas
        else:
            return None

    async def filter(
        self, adatas: List[AData], subscription: Subscription
    ) -> List[AData]:
        """
        过滤数据
        """
        result = []
        datas = await check_adatas(adatas, subscription)
        if datas:
            await save_adatas(datas, subscription)
        if subscription.white_keywords:
            for data in datas:
                for keyword in subscription.white_keywords:
                    title = data.title or ""
                    content = data.content or ""
                    if re.search(keyword, title) or re.search(keyword, content):
                        result.append(data)
        else:
            result = datas

        if subscription.black_keywords:
            for data in datas:
                for keyword in subscription.black_keywords:
                    title = data.title or ""
                    content = data.content or ""
                    if re.search(keyword, title) or re.search(keyword, content):
                        result.remove(data)

        return result

    async def handle_new_adata(
        self, adatas: List[BaseSpiderAData], subscription: Subscription
    ) -> List[BaseSpiderAData]:
        """
        处理数据
        """
        return adatas
