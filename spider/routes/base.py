"""
Spider 部分
"""
from typing import Callable, Optional, List
import arrow
from pydantic import BaseModel
from models import AData, Subscription
from utils import get_timestamp
from utils.request import get,Response



class BaseSpiderAData(AData):
    """
    Spider 数据模型 基类, 所有 Spider 数据模型都可以继承此类或者直接继承AData
    """
    def get_telegram_message_text(self)->str:
        """
        TelegramAction 的方法
        """
        return f"{self.title}\n{self.content}\n{self.url}"



class BaseSpider(BaseModel):
    """
    Spider 模型
    """

    name: str= "BaseSpider"
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


    def get_only_id(self,id) -> Optional[str]:
        """
        获取唯一id,带前缀
        """
        return f"{self.prefix}_{id}"

    async def request(self,subscription:Subscription) -> Optional[Response]:
        """
        请求数据
        
        """
        return await get(subscription.url)
    
    async def parse(self,subscription:Subscription,response:Response) -> Optional[List[BaseSpiderAData]]:
        """
        解析数据
        """
        return [BaseSpiderAData(id=self.get_only_id(get_timestamp()),title=subscription.name,content=f"{response.content[:100]}...",url=subscription.url,source=subscription.name,push_time=get_timestamp(),extend={})]
    
    async def start(self,subscription:Subscription) -> Optional[List[BaseSpiderAData]]:
        """
        开始流程
        """
        response = await self.request(subscription)
        if response:
            return await self.parse(subscription,response)
        else:
            return None

