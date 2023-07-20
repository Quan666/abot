import sys
from pydantic import BaseSettings
from typing import Optional,List
from loguru import logger



class EnvConfig(BaseSettings):
    env: str = "dev"
    class Config():
        # 设置需要识别的 .env 文件 判断当前环境
        env_file = ".env"
        # 设置字符编码
        env_file_encoding = 'utf-8'
env_config = EnvConfig()

class ConfigEnv():
    # 设置需要识别的 .env 文件 判断当前环境
    env_file = f".env.{env_config.env}"
    # 设置字符编码
    env_file_encoding = 'utf-8'

class Config(BaseSettings):

    # 日志等级
    log_level: str = "INFO"

    # 数据存储位置
    data_path: str = "data"
    # 日志存储位置
    log_path: str = "logs"

    # 代理
    proxy: Optional[str] = None

    web_host: str = "0.0.0.0"
    web_port: int = 8080

    telegram_api_id: Optional[str] = None
    telegram_api_hash: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_admin_ids: Optional[List[int]] = None

    class Config:
        # 设置需要识别的 .env 文件 判断当前环境
        env_file = f".env.{env_config.env}"
        # 设置字符编码
        env_file_encoding = 'utf-8'

config = Config()
# 配置日志等级
logger.remove()  # 清除默认的日志处理器
logger.add(sys.stderr, level=config.log_level)  # 将日志输出到终端，级别为 DEBUG
logger.add(
    f"{config.log_path}/{env_config.env}.log",
    level=config.log_level,
    rotation="1 day",
    retention="7 days",
    compression="zip",
    encoding="utf-8",
)

logger.debug(f"当前环境: {env_config.env}")
logger.debug(f"当前日志等级: {config.log_level}")
