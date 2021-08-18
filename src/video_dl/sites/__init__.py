"""List of Spiders."""
from urllib.parse import urlparse

from video_dl.spider import Spider
from .bilibili import BilibiliSpider

avaliable_spiders = [
    BilibiliSpider,
]

site2spider_dict = {spider.site: spider for spider in avaliable_spiders}


def choose_spider(url: str) -> Spider:
    """choose a spider for specific url."""
    parse_result = urlparse(url)
    netloc = parse_result.netloc

    for site, spider in site2spider_dict.items():
        if site in netloc:
            return spider()
