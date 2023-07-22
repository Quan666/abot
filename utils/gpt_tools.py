import json
from typing import List

import httpx
from loguru import logger
from config import config
from utils.request import proxy2httpx
import aiofiles
import os


async def request_gpt(messages: List[dict], model=config.gpt_model) -> dict:
    async with httpx.AsyncClient(proxies=proxy2httpx(config.proxy)) as client:
        response = await client.post(
            f"https://{config.gpt_host}/v1/chat/completions",
            json={
                "model": "gpt-3.5-turbo",
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


if not os.path.exists(config.data_path):
    os.mkdir(config.data_path)
if not os.path.exists(os.path.join(config.data_path, "cache")):
    os.mkdir(os.path.join(config.data_path, "cache"))

async def read_bangumi_name_cache() -> List[dict]:
    """
    读取缓存 
    存储在 data/cache/bangumi_name_cache.json
    """
    try:
        async with aiofiles.open(
            os.path.join(config.data_path, "cache", "bangumi_name_cache.json"),
            mode="r",
            encoding="utf-8",
        ) as f:
            bangumi_name_cache = await f.read()
        return json.loads(bangumi_name_cache)
    except Exception as e:
        return []
    
async def write_bangumi_name_cache(bangumi_name_cache: List[dict]) -> None:
    """
    写入缓存
    """
    async with aiofiles.open(
        os.path.join(config.data_path, "cache", "bangumi_name_cache.json"),
        mode="w",
        encoding="utf-8",
    ) as f:
        await f.write(json.dumps(bangumi_name_cache, ensure_ascii=False, indent=4))


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

    bangumi_name_cache = await read_bangumi_name_cache()

    # 遍历缓存
    for cache in bangumi_name_cache:
        cn = cache.get("cn", "")
        jp = cache.get("jp", "")
        if not cn and not jp:
            continue
        if cn in text or jp in text:
            return cache

    # 如果相似度小于设定值，请求 chatgpt
    try:
        gpt_result = await find_bangumi_name(text)
        if not gpt_result["cn"] and not gpt_result["jp"]:
            return {"cn": None, "jp": None}
        # 存储到缓存
        bangumi_name_cache = await read_bangumi_name_cache()
        bangumi_name_cache.append(gpt_result)
        await write_bangumi_name_cache(bangumi_name_cache)
        return gpt_result
    except Exception as e:
        logger.error(f"find_bangumi_name_cache error: {e}")
        return {"cn": None, "jp": None}
