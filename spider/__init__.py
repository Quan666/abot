
import re
from typing import Optional

from models import Subscription
from spider.routes.base import BaseSpider


SPIDES = []

def register_spider(spider_cls):
    SPIDES.append(spider_cls)


def get_spider(subscription:Subscription)->Optional[BaseSpider]:
    for spider in SPIDES:
        if re.match(spider.url_pattern, subscription.url):
            return spider
    return None

register_spider(BaseSpider())