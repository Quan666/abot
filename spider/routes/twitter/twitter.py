"""
Spider部分
"""
import json
from typing import Optional, List
import arrow
from models import Subscription
from spider.routes.base import BaseSpider, BaseSpiderAData
from utils import timestamp2human
from utils.request import Response
from difflib import SequenceMatcher
from config import config


class TwitterSpiderAData(BaseSpiderAData):
    """
    TwitterSpider 数据模型
    """

    pic_url: Optional[List[str]] = []


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


class TwitterSpider(BaseSpider):
    """
    Spider 模型
    """

    name: str = "TwitterSpider"
    """
    Spider 名称
    """

    description: Optional[str] = "Twitter"
    """
    描述
    """

    url_pattern: str = "twitter"
    """
    url 匹配正则表达式
    """

    prefix: str = "TwitterSpider"
    """
    唯一id 前缀
    """

    async def parse(
        self, subscription: Subscription, response: Response
    ) -> Optional[List[TwitterSpiderAData]]:
        """
        解析数据
        """
        result = []
        d = json.loads(response.content)
        if items := d.get("data"):
            for item in items:
                pic_url = []
                if media:=item.get("entities", {}).get("media",[]):
                    for m in media:
                        if m.get("type") == "photo" and m.get("media_url_https"):
                            pic_url.append(m.get("media_url_https"))

                adata = TwitterSpiderAData(
                    id=self.get_only_id(item.get("id")),
                    title=item.get("text"),
                    content=item.get("text"),
                    url=f"https://twitter.com/{item.get('user',{}).get('screen_name')}/status/{item.get('id')}",
                    source=f"Twitter - <a href='https://twitter.com/{item.get('user',{}).get('screen_name')}'>{item.get('user',{}).get('name')}</a>",
                    push_time=int(
                        arrow.get(item.get("created_at")).float_timestamp * 1000
                    ),
                    extend=item,
                    pic_url=pic_url,
                )
                result.append(adata)
        return result
