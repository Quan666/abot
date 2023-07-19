"""
机器人模块
"""

from typing import Any, Literal, Optional, Tuple

from loguru import logger
from telethon import TelegramClient, events, sync, Button

from config import config

proxy = Optional[Tuple[Literal["http"], str, int]]

if config.proxy:
    proxy = (
        "http",
        config.proxy.split(":")[0],
        int(config.proxy.split(":")[1]),
    )

bot:Optional[TelegramClient] = None

def get_bot() -> TelegramClient:
    """
    获取 bot
    """
    if not bot:
        raise Exception("bot 未初始化")
    return bot

async def start_telegram_bot(loop: Any, boot_message: str) -> None:
    if not (
        config.telegram_api_id
        and config.telegram_api_hash
        and config.telegram_bot_token
    ):
        logger.warning("Telegram Bot 未配置")
        return
    global bot
    bot = TelegramClient(
        "bot",
        config.telegram_api_id,
        config.telegram_api_hash,
        proxy=proxy,
        loop=loop,
    )
    from . import command
    logger.success("Telegram Bot 初始化成功")
    await bot.start(bot_token=config.telegram_bot_token)
    if config.telegram_admin_ids:
        await bot.send_message(
            config.telegram_admin_ids[0],
            boot_message,
        )
    await bot.run_until_disconnected()