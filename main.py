from config import config
from bot import start_telegram_bot
from subscription import start_subscription
from web import start_web
import asyncio
from loguru import logger

async def background_task():
    await asyncio.gather(
        start_telegram_bot(asyncio.get_event_loop(), "ABot Started"),
        start_subscription(),
    )

if __name__ == "__main__":
    logger.success("程序启动")
    try:
        asyncio.run(background_task())
        # start_web()
    except KeyboardInterrupt:
        logger.error("程序退出")
        exit(0)
    
