from pydantic import BaseModel
from typing import Any, List, Optional


class PikPakDownloadInfo(BaseModel):
    """
    PikPak 下载信息
    """

    save_path: str
    """
    保存路径, 例如: /data/xx/download, 必须以 / 开头
    """

    file_url: str
    """
    文件链接, magnet链接 or http链接
    """
