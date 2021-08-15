from aiohttp import ClientSession
import asyncio
import os
import subprocess
import time

from prettytable import PrettyTable
import aiofiles

from toolbox import CONFIG


class Media(object):
    """音视频资源类"""
    chunk_size = CONFIG.chunk_size

    def __init__(self, url: str, name: str, size: float, desc: str = 'null'):
        """初始化音视频资源对象

        @param url: 在线访问网址
        @param file_name: 存储时文件名
        @param size: 文件大小
        @param description: 描述文本
        """
        self.url = url
        self.name = name
        self.size = size
        self.desc = desc

        # 目标存储路径
        self.target = None

    async def download(self, session: ClientSession, folder: str) -> None:
        """下载音视频资源到存储路径

        @param session: 用以访问互联网的会话管理器
        @param folder: 存储路径
        """
        # 确定存储位置
        self.target = os.path.join(folder, self.name)
        print(f'正在将 {self.name} 下载到 {self.target} ...')

        # 进度条起始信息
        current = 0  # 当前已下载数据量
        last_time = time.time()  # 启动下载时的时间戳
        async with session.get(url=self.url) as r:
            # 从响应头中获取文件总大小
            total_volume = int(r.headers['Content-Length'])
            async with aiofiles.open(self.target, 'wb') as f:
                async for chunk in r.content.iter_chunked(self.chunk_size):
                    await f.write(chunk)

                    # 进度条相关配置
                    current += self.chunk_size
                    progress = int(current / total_volume * 100)
                    now = time.time()
                    speed = self.chunk_size / (now - last_time) / 1024 / 1024
                    last_time = now
                    print(
                        '\r',  # 回退当前行最左侧
                        f'{self.name[-30:]}: ',  # 标明文件名
                        f'{current / 1024 / 1024:6.2f}',  # 已下载文件大小
                        '/',
                        f'{total_volume / 1024 / 1024:6.2f}MB',  # 文件总大小
                        f'({speed:6.2f}MB/S)|',  # 下载速度
                        'x' * progress, '.' * (100 - progress),  # 简易进度条
                        f'|({progress}%)',  # 已下载百分比
                        sep='', end=''
                    )


class MediaCollection(list):
    """音视频资源列表类"""
    def __init__(self, members: list = []):
        super().__init__(members)

    async def download(self, session: ClientSession, folder: str) -> None:
        """下载资源列表当中的所有资源

        @param session: 用于访问互联网的会话管理器
        @param folder: 存储路径
        """
        self.folder = folder
        tasks = [
            asyncio.create_task(item.download(session, folder))
            for item in self
        ]
        await asyncio.wait(tasks)
        print('\n当前资源列表内所有数据均已下载完毕！')

    def __str__(self):
        """用更加漂亮的方式打印资源列表"""
        tb = PrettyTable()
        tb.field_names = ['index', 'name', 'desc', 'size', 'url']
        for index, media in enumerate(self, 1):
            info = [index, media.name, media.desc, media.size, media.url[:40]]
            tb.add_row(info)

        return tb.get_string()

    def merge(self, target: str) -> None:
        """将资源列表当中所有资源合并成一个视频

        @param target: 视频存储路径
        """
        print(f'正在将资源列表当中的内容合并到 {target} ...')
        cmd = ['ffmpeg']
        for item in self:
            cmd += ['-i', item.target]
        cmd += ['-codec', 'copy', target, '-y']
        subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )

        # 删除临时文件
        for item in self:
            os.remove(item.target)
