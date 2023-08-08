import base64
from typing import Optional

import httpx

from utils.request import proxy2httpx


async def download_torrent(url: str, proxy: Optional[str] = None) -> Optional[bytes]:
    """
    下载torrent文件
    """
    async with httpx.AsyncClient(proxies=proxy2httpx(proxy)) as client:
        try:
            resp = await client.get(url)
            return resp.content
        except Exception as e:
            raise Exception(f"{url} 下载失败: {e}")


def get_torrent_b16_hash(content: bytes) -> str:
    import magneturi

    # mangetlink = magneturi.from_torrent_file(torrentname)
    manget_link = magneturi.from_torrent_data(content)
    # print(mangetlink)
    ch = ""
    n = 20
    b32_hash = n * ch + manget_link[20:52]
    # print(b32Hash)
    b16_hash = base64.b16encode(base64.b32decode(b32_hash))
    b16_hash = b16_hash.lower()
    # print("40位info hash值：" + '\n' + b16Hash)
    # print("磁力链：" + '\n' + "magnet:?xt=urn:btih:" + b16Hash)
    return str(b16_hash, "utf-8")


def torrent_file2magnet_url(content: bytes) -> str:
    import magneturi

    manget_link = magneturi.from_torrent_data(content)
    return manget_link
