"""Library for Control flow."""
import asyncio
import platform
import time

from video_dl.args import Arguments
from video_dl.spider import Spider
from video_dl.toolbox import info
import video_dl.sites  # pylint: disable=W0611


if platform.system() != 'Windows':
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
else:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def main():
    # get url from command line's augument and create a specifc spider.
    spider = Spider.create(Arguments().url)

    # start spider and download video.
    start_time = time.time()
    asyncio.run(spider.run())

    info('done', f'had wasted your time: {time.time() - start_time:.2f}s!')
