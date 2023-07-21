import asyncio
from typing import Callable, Optional
from fastapi import FastAPI
from config import config
import uvicorn
from loguru import logger

web_app = FastAPI()

from . import routes

web_app.include_router(routes.router)


# 启动函数
def start_web():
    uvicorn.run(
        web_app,
        host=config.web_host,
        port=config.web_port,
    )
