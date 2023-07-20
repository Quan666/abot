"""
Spider部分
"""
from typing import Callable, Optional, List
import arrow
from pydantic import BaseModel
from models import AData, Subscription
from spider.routes.base import BaseSpider
from utils import get_timestamp
from utils.request import get,Response



class RssSpiderAData(AData):
    """
    Spider 数据模型
    """
    def get_telegram_message_text(self)->str:
        """
        TelegramAction 的方法
        """
        return f"{self.title}\n{self.content}\n{self.url}"



class RssSpider(BaseSpider):
    """
    Spider 模型
    """

    name: str= "RssSpider"
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


    async def request(self,subscription:Subscription) -> Optional[Response]:
        """
        请求数据
        
        """
        return await get(subscription.url)
    
    async def parse(self,subscription:Subscription,response:Response) -> Optional[List[RssSpiderAData]]:
        """
        解析数据
        """
        return [RssSpiderAData(id=self.get_only_id(get_timestamp()),title=subscription.name,content=f"{response.content[:100]}...",url=subscription.url,source=subscription.name,push_time=get_timestamp(),extend={})]
    
    
    async def start(self,subscription:Subscription) -> Optional[List[RssSpiderAData]]:
        """
        开始流程
        """
        response = await self.request(subscription)
        if response:
            return await self.parse(subscription,response)
        else:
            return None

