import json
import os
from typing import Any
import aiofiles

from config import config

if not os.path.exists(config.data_path):
    os.mkdir(config.data_path)
if not os.path.exists(os.path.join(config.data_path, "cache")):
    os.mkdir(os.path.join(config.data_path, "cache"))


async def read_cache(key: str) -> Any:
    """
    读取缓存
    存储在 data/cache/{key}.json
    """
    try:
        async with aiofiles.open(
            os.path.join(config.data_path, "cache", f"{key}.json"),
            mode="r",
            encoding="utf-8",
        ) as f:
            bangumi_name_cache = await f.read()
        return json.loads(bangumi_name_cache)
    except Exception as e:
        return None


async def write_cache(key: str, data: Any) -> None:
    """
    写入缓存
    """
    async with aiofiles.open(
        os.path.join(config.data_path, "cache", f"{key}.json"),
        mode="w",
        encoding="utf-8",
    ) as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=4))
