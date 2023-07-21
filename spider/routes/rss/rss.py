"""
Spider部分
"""
from contextlib import suppress
from typing import Any, Callable, Dict, Optional, List
import arrow
from pydantic import BaseModel
from models import AData, Subscription
from spider.routes.base import BaseSpider, BaseSpiderAData
from utils import get_timestamp, timestamp2human
from utils.request import get, Response
import feedparser
from email.utils import parsedate_to_datetime
from difflib import SequenceMatcher
from config import config


class RssSpiderAData(BaseSpiderAData):
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
        similarity = SequenceMatcher(None, self.content[: len(self.title)], self.title)
        if similarity.ratio() <= 0.6:
            text += f"<b>{self.title}</b>\n"
        text += f"{self.content}\n\n"
        text += f"<a href='{self.url}'>阅读原文</a>"
        return text

    async def get_telegram_message_config(self) -> str:
        """
        TelegramAction 的方法, 发送消息时的配置
        """
        return {
            "parse_mode": "html",
        }


class RssSpider(BaseSpider):
    """
    Spider 模型
    """

    name: str = "RssSpider"
    """
    Spider 名称
    """

    description: Optional[str] = "RSS"
    """
    描述
    """

    url_pattern: str = ".*?"
    """
    url 匹配正则表达式
    """

    prefix: str = "RssSpider"
    """
    唯一id 前缀
    """

    async def parse(
        self, subscription: Subscription, response: Response
    ) -> Optional[List[RssSpiderAData]]:
        """
        解析数据
        """
        result = []
        d = feedparser.parse(response.content)
        if d.get("feed"):
            for entry in d["entries"]:
                adata = RssSpiderAData(
                    id=self.get_only_id(
                        entry.get("guid ", entry.get("link", entry.get("title")))
                    ),
                    title=entry["title"],
                    content=entry["summary"],
                    url=entry.get("link", None),
                    source=d["feed"]["title"],
                    push_time=await handle_date(entry),
                    extend=entry,
                )
                result.append(adata)
        return result


def get_item_date(item: Dict[str, Any]) -> arrow.Arrow:
    if date := item.get("published", item.get("updated")):
        with suppress(Exception):
            date = parsedate_to_datetime(date)
        return arrow.get(date)
    return arrow.now()


async def handle_date(item: Dict[str, Any]) -> int:
    date = get_item_date(item)
    return int(date.float_timestamp * 1000)
