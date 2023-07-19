import arrow


def get_timestamp()->int:
    """
    获取当前时间戳, 13 位
    """
    return int(arrow.now().float_timestamp * 1000)