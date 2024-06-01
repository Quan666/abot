"""
Spider部分
"""

from typing import Optional, List
import arrow
from loguru import logger
from telethon import TelegramClient, events
from src.bot.lib import InputListInt, InputListStr
from src.models import Subscription
from src.spider.routes.base import BaseSpider, BaseSpiderAData, BaseSpiderDynamicConfig
from src.utils import get_timestamp, timestamp2human
from src.utils.request import Response
from config import config


class SSLCheckSpiderAData(BaseSpiderAData):
    """
    Spider 数据模型
    """

    async def get_telegram_message_text(self) -> str:
        """
        TelegramAction 的方法
        生成Telegram消息文本, 支持Markdown
        """
        text = f"<i>{self.source}</i>\n"
        text += f"{timestamp2human(self.push_time)}\n\n"
        text += f"{self.content}\n\n"
        return text

    async def get_telegram_message_config(self) -> str:
        """
        TelegramAction 的方法, 发送消息时的配置
        """
        return {
            "parse_mode": "html",
        }


class SSLCheckSpiderDynamicConfig(BaseSpiderDynamicConfig):
    """
    动态配置
    """

    domains: List[str] = []
    """
    域名列表
    """

    expired_days: List[int] = [30, 15, 7, 3, 1]
    """
    过期推送节点
    """

    async def telegram_setting(
        self,
        bot: TelegramClient,
        event: events.CallbackQuery.Event,
    ) -> None:
        """
        动态配置, Telegram 交互设置, 继承此类需要重写
        """
        self.domains = await InputListStr(
            bot,
            event,
            f"输入需要监控的域名: ",
            self.domains,
        ).input()
        self.expired_days = await InputListInt(
            bot,
            event,
            f"输入距离过期多少天时推送消息: ",
            self.expired_days,
        ).input()

    async def telegram_text(self):
        """
        Telegram 配置展示文本, 继承此类 可以选择
        """
        tmp = "域名列表:\n"
        tmp += "\n".join([f"  - {d}" for d in self.domains])
        tmp += "\n\n"
        tmp += "推送节点:\n"
        tmp += "\n".join([f"  - {d} 天" for d in self.expired_days])
        return f"{tmp if tmp.strip() else '  无'}"


class SSLCheckSpider(BaseSpider):
    """
    Spider 模型
    """

    name: str = "SSLCheckSpider"
    """
    Spider 名称
    """

    description: Optional[str] = "SSL有效期"
    """
    描述
    """

    url_pattern: str = ".*?"
    """
    url 匹配正则表达式
    """

    prefix: str = "SSLCheckSpider"
    """
    唯一id 前缀
    """

    dynamic_config: Optional[SSLCheckSpiderDynamicConfig] = (
        SSLCheckSpiderDynamicConfig()
    )
    """
    动态配置
    """

    async def request(self, subscription: Subscription) -> Optional[Response]:
        """
        请求数据

        """
        proxy = None
        if subscription.enable_proxy:
            proxy = config.proxy
        try:
            result = []
            for domain in self.dynamic_config.domains:
                result.append(await check_ssl_certificate_expiration(domain))
            return Response(
                content=result,
                status_code=200,
                headers={},
                url="",
            )
        except Exception as e:
            logger.error(f"Spider {self.name} request error: {e}")
            return None

    async def parse(
        self, subscription: Subscription, response: Response
    ) -> Optional[List[SSLCheckSpiderAData]]:
        """
        解析数据
        """
        result = []
        texts = []
        for item in response.content:
            # 剩余过期天数
            day = (
                arrow.get(item["not_after"]).to("local") - arrow.now().to("local")
            ).days
            if day in self.dynamic_config.expired_days or day <= 0:
                text = ""
                # 过期域名前面加上 ❌，未过期的加上 ✅
                tmp = "✅ "
                # 小于 7 天的加上 ⚠️
                if day <= 7:
                    tmp = "⚠️ "
                if day <= 0:
                    tmp = "❌过期 "
                text += f"{tmp}{item['hostname']}\n"
                text += f"有效期: {arrow.get(item['not_after']).to('local')}\n"
                # 剩余天数
                text += f"剩余: {day} 天\n"
                texts.append(text)
        if texts:
            result.append(
                SSLCheckSpiderAData(
                    title="",
                    content="\n\n".join(texts),
                    source=f"域名 SSL 证书过期提醒",
                    push_time=get_timestamp(),
                    url=None,
                    id=self.get_only_id(get_timestamp()),
                )
            )
        return result


import ssl
import datetime
import asyncio


async def check_ssl_certificate_expiration(hostname, port=443) -> dict:
    """
    检查SSL证书有效期

    """
    # 创建 SSL 上下文
    context = ssl.create_default_context()

    # 连接到指定主机并获取 SSL 证书
    try:
        reader, writer = await asyncio.open_connection(hostname, port, ssl=context)
        cert = writer.get_extra_info("ssl_object").getpeercert()

        # 获取证书的有效期信息
        not_before = datetime.datetime.strptime(
            cert["notBefore"], "%b %d %H:%M:%S %Y %Z"
        )
        not_after = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")

        # 获取当前时间
        current_time = datetime.datetime.now()

        # 转化为时间戳 13位
        return {
            "hostname": hostname,
            "not_before": int(not_before.timestamp() * 1000),
            "not_after": int(not_after.timestamp() * 1000),
            "expired": not (not_before <= current_time <= not_after),
            # 其他信息
            "info": cert,
            "error": None,
        }
    except Exception as e:
        return {
            "hostname": hostname,
            "not_before": None,
            "not_after": None,
            "expired": None,
            # 其他信息
            "info": None,
            "error": f"{e}",
        }
