import httpx
from typing import Optional

from utils.request import proxy2httpx


async def pic_download(
    url, params=None, headers=None, cookies=None, timeout=10, proxy=None
) -> Optional[bytes]:
    """
    proxy: 代理, 格式为: 127.0.0.1:7890
    """
    # 增加 Referer
    if headers is None:
        headers = {}
    headers["Referer"] = url
    async with httpx.AsyncClient(proxies=proxy2httpx(proxy)) as client:
        try:
            resp = await client.get(
                url, params=params, headers=headers, cookies=cookies, timeout=timeout
            )
            return resp.content
        except httpx.ConnectError as e:
            if str(e) == "":
                e = "超时"
            raise Exception(f"{url} 连接失败: {e}")

        except Exception as e:
            raise Exception(f"{url} 请求失败: {e}")

