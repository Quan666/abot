from pydantic import BaseModel
from typing import Any, List, Optional



class AData(BaseModel):
    """
    通用数据模型
    """

    id: str
    """
    唯一标识符

    格式为: {prefix}_{id}

    用于去重复,不同Spider前缀不同

    """

    title: Optional[str] = None
    """
    标题
    """

    content: Optional[str] = None
    """
    内容
    """

    url: Optional[str] = None
    """
    链接
    """

    source: Optional[str] = None
    """
    来源
    """

    push_time: Optional[int] = None
    """
    推送时间, 13 位时间戳
    """

    extend: Optional[dict] = None
    """
    扩展字段
    """

    


class Subscription(BaseModel):
    """
    订阅模型
    """

    name: str
    """
    订阅名称
    """

    url : str
    """
    订阅链接
    """

    cron : str
    """
    订阅更新时间
    """

    spider_name: str
    """
    Spider 名称
    """
    
    actions: List[Any]
    """
    订阅Acton

    会触发哪些动作，比如: telegram, webhook
    对应的动作动态配置
    """
    
    def to_json(self):
        return self.dict()


class Response(BaseModel):
    """
    统一响应模型
    """

    status_code: int
    """
    状态码
    """

    content: str
    """
    响应内容
    """

    headers: dict
    """
    响应头
    """



    def is_success(self) -> bool:
        """
        判断是否成功, 200-299 为成功
        """
        return 200 <= self.status_code < 300