import json
from typing import List

import httpx
from loguru import logger
from config import config
from src.utils.cache import read_cache, write_cache
from src.utils.request import proxy2httpx
import aiofiles
import os


async def request_gpt(messages: List[dict], model=config.gpt_model) -> dict:
    async with httpx.AsyncClient(proxies=proxy2httpx(config.proxy)) as client:
        response = await client.post(
            f"https://{config.gpt_host}/v1/chat/completions",
            json={
                "model": "gpt-4o-mini",
                "messages": messages,
            },
            headers={"Authorization": f"Bearer {config.gpt_api_key}"},
        )
        return response.json()


async def find_bangumi_name(text: str) -> dict:
    """
    通过 chatgpt 识别番剧名称
    """
    system = """
        input:
        [Lilith-Raws] AI 电子基因 / AI no Idenshi - 03 [Baha][WebDL 1080p AVC AAC][CHT]
        Only output json, only bangumi cn and jp fields:
        ok:{"cn": "AI 电子基因","jp": "AI no Idenshi"}
        error:{"cn": null,"jp": null}
        more example:
        [ANi] 番剧名称没日文 - 03 [1080P][Baha][WEB-DL][AAC AVC][CHT][MP4]
        {"cn": "番剧名称没日文","jp": null}
        """
    # 去掉每行前面的空格
    system = "\n".join([i.strip() for i in system.split("\n")])

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]
    response = await request_gpt(messages)
    logger.debug(f"find_bangumi_name chatgpt response: {response}")
    return json.loads(response["choices"][0]["message"]["content"])


async def find_bangumi_name_cache(text: str) -> dict:
    """
    通过 chatgpt 识别番剧名称, 使用缓存
    通过 相似度判断是否走缓存
    缓存格式:
    {
        "cn": "AI 电子基因",
        "jp": "AI no Idenshi"
    }
    """
    CACHE_KEY = "bangumi_name_cache"
    if not text:
        return {"cn": None, "jp": None}
    bangumi_name_cache = await read_cache(CACHE_KEY) or []

    # 遍历缓存
    for cache in bangumi_name_cache:
        cn = cache.get("cn", "")
        jp = cache.get("jp", "")
        if not cn and not jp:
            continue
        if (cn and cn in text) or (jp and jp in text):
            return cache

    # 如果相似度小于设定值，请求 chatgpt
    try:
        gpt_result = await find_bangumi_name(text)
        if not gpt_result["cn"] and not gpt_result["jp"]:
            return {"cn": None, "jp": None}
        # 存储到缓存
        bangumi_name_cache = await read_cache(CACHE_KEY) or []
        bangumi_name_cache.append(gpt_result)
        await write_cache(CACHE_KEY, bangumi_name_cache)
        return gpt_result
    except Exception as e:
        logger.error(f"find_bangumi_name_cache error: {e}")
        return {"cn": None, "jp": None}
