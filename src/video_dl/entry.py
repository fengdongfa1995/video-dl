"""Library for Control flow."""
import asyncio
import platform
import time

from video_dl.args import Arguments
from video_dl.spider import Spider


if platform.system() != 'Windows':
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def main():
    spider = Spider.create_spider(Arguments().url)
    start_time = time.time()
    asyncio.run(spider.run())
    print(f'job done! just wasted your time: {time.time() - start_time:.2f}s!')


if __name__ == '__main__':
    main()
