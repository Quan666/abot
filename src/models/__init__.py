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

    cron: str
    """
    订阅更新时间
    """

    spider: Any
    """
    Spider
    """

    actions: List[Any]
    """
    订阅Acton

    会触发哪些动作，比如: telegram, webhook
    对应的动作动态配置
    """

    enable: bool = True
    """
    是否启用订阅
    """

    enable_proxy: bool = False
    """
    是否启用代理
    """

    white_keywords: Optional[List[str]] = []
    """
    白名单关键词, 满足其中一个关键词则推送, 为空则不限制
    支持正则表达式
    """

    black_keywords: Optional[List[str]] = []
    """
    黑名单关键词, 满足其中一个关键词则不推送, 为空则不限制
    支持正则表达式
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

    content: Any
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
