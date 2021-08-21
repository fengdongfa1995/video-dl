"""Extarct information from html source code."""


class Extractor(object):
    """Base class of Extractors."""
    @classmethod
    def create(cls, url: str):
        """return a specific Extractor depends on url."""
        for subclass in cls.__subclasses__():
            for pattern in subclass.pattern:
                if pattern.search(url):
                    return subclass()
        raise NotImplementedError
