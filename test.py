from config import config
import asyncio
from loguru import logger

from utils.gpt_tools import find_bangumi_name_cache, find_bangumi_name


def find_bangumi_name_cache_test():
    text = (
        "[ANi] 成为悲剧元凶的最强异端，最后头目女王为了人民牺牲奉献 - 03 [1080P][Baha][WEB-DL][AAC AVC][CHT][MP4]"
    )

    async def _():
        logger.info(await find_bangumi_name_cache(text))

    asyncio.run(_())


def find_bangumi_name_test():
    text = (
        "[ANi] 成为悲剧元凶的最强异端，最后头目女王为了人民牺牲奉献 - 03 [1080P][Baha][WEB-DL][AAC AVC][CHT][MP4]"
    )

    async def _():
        logger.info(await find_bangumi_name(text))

    asyncio.run(_())


if __name__ == "__main__":
    # find_bangumi_name_cache_test()
    find_bangumi_name_test()
