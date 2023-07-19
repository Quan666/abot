"""
行为模块
每个行为模块都是一个类，继承自Action类
包含触发条件、执行动作、配置信息（包括固定配置，和动态配置，动态配置为订阅时配置，如触发条件）
"""

from typing import List,Optional 
from pydantic import BaseModel,BaseSettings
from loguru import logger
from config import ConfigEnv
from models import AData, Subscription

__ACTION_NAME__ = "BaseAction"
__FUNC_LIST__: Optional[List[str]] = []
"""
Action 需要支持的方法列表
"""

class BaseActionStaticConfig(BaseSettings):
    """
    静态配置
    """
    log_prefix: Optional[str] = "BaseAction["

    class Config(ConfigEnv):
        # 解析的前缀
        env_prefix = "BASE_ACTION_"

class BaseActionDynamicConfig(BaseModel):
    """
    动态配置
    """



class BaseAction(BaseModel):
    """
    Action基类, 所有Action都需要继承此类并重写 name, description, execute 方法
    """

    name: Optional[str]= __ACTION_NAME__
    """
    行为名称
    """

    description: Optional[str] = "基础Action"
    """
    行为描述
    """


    static_config: Optional[BaseActionStaticConfig] = BaseActionStaticConfig()
    """
    静态配置
    """

    dynamic_config: Optional[BaseActionDynamicConfig] = BaseActionDynamicConfig()
    """
    动态配置
    """

    
    async def execute(self, datas: List[AData], subscription: Subscription) -> None:
        """
        执行
        """
        logger.info(f"{self.static_config.log_prefix}{self.name}执行")
    
