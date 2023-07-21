import httpx
from models import Response


def proxy2httpx(proxy: str) -> dict:
    """
    代理转换为 httpx 格式
    """
    if not proxy:
        return {}
    return {
        "http://": f"http://{proxy}",
        "https://": f"http://{proxy}",
    }


async def get(
    url, params=None, headers=None, cookies=None, timeout=10, proxy=None
) -> Response:
    """
    proxy: 代理, 格式为: 127.0.0.1:7890
    """
    async with httpx.AsyncClient(proxies=proxy2httpx(proxy)) as client:
        try:
            resp = await client.get(
                url, params=params, headers=headers, cookies=cookies, timeout=timeout
            )
            return Response(
                status_code=resp.status_code,
                content=resp.text,
                headers=resp.headers,
            )
        except httpx.ConnectError as e:
            if str(e) == "":
                e = "超时"
            raise Exception(f"{url} 连接失败: {e}")

        except Exception as e:
            raise Exception(f"{url} 请求失败: {e}")


async def post(
    url, data=None, json=None, headers=None, cookies=None, timeout=10, proxy=None
) -> Response:

    async with httpx.AsyncClient(proxies=proxy2httpx(proxy)) as client:
        try:
            resp = await client.post(
                url,
                data=data,
                json=json,
                headers=headers,
                cookies=cookies,
                timeout=timeout,
            )
            return Response(
                status_code=resp.status_code,
                content=resp.text,
                headers=resp.headers,
            )
        except Exception as e:
            raise Exception(f"{url} 请求失败: {e}")
