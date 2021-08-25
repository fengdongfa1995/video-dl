"""Extract information from html source code.

Typical usage:
    url = 'https://www.bilibili.com/video/BV15L411p7M8'
    extractor = Extractor.create(url)  # will return a BilibiliVideoExtractor
"""


class Extractor(object):
    """Base class of Extractors.

    subclass of Extractor should provide a public attribute:
        pattern: Extractor will use this list to create a specific Spider for target url.
         For example, BilibiliVideoExtractor's pattern is [re.compile('bilibili.com/video/BV.*')],
         will auto match to a url like 'https://www.bilibili.com/video/BV346'.
    """
    @classmethod
    def create(cls, url: str):
        """return a specific Extractor depends on url."""
        for subclass in cls.__subclasses__():
            for pattern in subclass.pattern:
                if pattern.search(url):
                    return subclass()
        raise NotImplementedError
