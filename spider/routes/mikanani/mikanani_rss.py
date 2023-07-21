"""
Spider部分
"""
from contextlib import suppress
import re
from typing import Any, Callable, Dict, Optional, List
import arrow
from pydantic import BaseModel
from models import AData, Subscription
from spider.routes.base import BaseSpider, BaseSpiderAData
from utils import convert_size, get_timestamp, timestamp2human
from utils.request import Response
import feedparser
from email.utils import parsedate_to_datetime
from difflib import SequenceMatcher
from config import config


class MikananiRssSpiderAData(BaseSpiderAData):
    """
    Spider 数据模型
    """

    torrent_url: Optional[str] = None
    """
    种子链接
    """
    content_length: int = 0
    """
    种子大小
    """
    magnet_url: Optional[str] = None

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

        # 磁力链接
        if self.magnet_url:
            text += f"<code>{self.magnet_url}</code>\n"
        # 种子大小
        if self.content_length:
            text += f"大小: {convert_size(self.content_length)}\n"
        # 种子链接
        if self.torrent_url:
            text += f"<a href='{self.torrent_url}'>下载种子</a>  "

        text += f"<a href='{self.url}'>阅读原文</a>"
        return text

    async def get_telegram_message_config(self) -> str:
        """
        TelegramAction 的方法, 发送消息时的配置
        """
        return {
            "parse_mode": "html",
        }


class MikananiRssSpider(BaseSpider):
    """
    Spider 模型
    """

    name: str = "MikananiRss"
    """
    Spider 名称
    """

    description: Optional[str] = "Mikanani RSS"
    """
    描述
    """

    url_pattern: str = "mikanani"
    """
    url 匹配正则表达式
    匹配 mikanani
    """

    prefix: str = "MikananiRssSpider"
    """
    唯一id 前缀
    """

    async def parse(
        self, subscription: Subscription, response: Response
    ) -> Optional[List[MikananiRssSpiderAData]]:
        """
        解析数据
        """
        result = []
        d = feedparser.parse(response.content)
        if d.get("feed"):
            for entry in d["entries"]:
                torrent_url = get_torrent_url(entry)
                adata = MikananiRssSpiderAData(
                    id=self.get_only_id(entry.get("link", entry.get("title"))),
                    title=entry["title"],
                    content=entry["summary"],
                    url=entry.get("link", None),
                    source=d["feed"]["title"],
                    push_time=await handle_date(entry),
                    extend=entry,
                    content_length=int(entry.get("contentlength", 0)),
                    torrent_url=torrent_url,
                    magnet_url=torrent_url2magnet_url(torrent_url),
                )
                result.append(adata)
        return result


def get_torrent_url(entry: Dict[str, Any]) -> Optional[str]:
    for link in entry.get("links", []):
        if link["type"] == "application/x-bittorrent":
            return link["href"]
    return None


def torrent_url2magnet_url(url: Optional[str]) -> Optional[str]:
    if url:
        # 正则匹配出hash
        hash_code = re.search(r"[0-9a-fA-F]{40}", url)
        if hash_code:
            return f"magnet:?xt=urn:btih:{hash_code.group()}"
    return None


def get_item_date(item: Dict[str, Any]) -> arrow.Arrow:
    if date := item.get("published"):
        with suppress(Exception):
            date = parsedate_to_datetime(date)
        return arrow.get(date)
    return arrow.now()


async def handle_date(item: Dict[str, Any]) -> int:
    date = get_item_date(item)
    return int(date.float_timestamp * 1000)