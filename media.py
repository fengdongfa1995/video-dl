from aiohttp import ClientSession
import asyncio
import os
import subprocess

from prettytable import PrettyTable
import aiofiles

from toolbox import CONFIG


class Media(object):
    """音视频资源类"""
    chunk_size = CONFIG.chunk_size

    # 控制并发量
    sema = asyncio.Semaphore(CONFIG.max_conn)

    # 文件大小超过阈值做分段下载
    threshold = CONFIG.big_file_threshold

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

        # 当前已下载大小
        self.current_size = 0

    async def _get_file_size(self, session: ClientSession) -> None:
        """通过发送head请求获取目标文件大小"""
        headers = {'range': 'bytes=0-1'}
        async with self.sema:
            async with session.get(url=self.url, headers=headers) as r:
                self.size = int(r.headers['Content-Range'].split('/')[1])

    async def download(self, session: ClientSession, folder: str) -> None:
        """下载音视频资源到存储路径

        @param session: 用以访问互联网的会话管理器
        @param folder: 存储路径
        """
        # 确定存储位置
        self.target = os.path.join(folder, self.name)
        print(f'正在将 {self.name} 下载到 {self.target} ...')

        # 获取文件大小
        await self._get_file_size(session)

        if self.size <= self.threshold:
            await self._download_clip(session, folder)
        else:
            clip_point = range(0, self.size, self.threshold)
            tasks = []
            targets = []
            for index, value in enumerate(clip_point, 1):
                end_point = min(value + self.threshold - 1, self.size - 1)
                d, n = os.path.splitext(self.target)
                target = f'{d}_part_{index}{n}'
                tasks.append(asyncio.create_task(
                    self._download_clip(
                        session, folder,
                        {'range': f'bytes={value}-{end_point}'},
                        target
                    )))
                targets.append(target)
            await asyncio.wait(tasks)

            # 合并音视频文件碎片
            async with aiofiles.open(self.target, 'wb') as f:
                for t in targets:
                    async with aiofiles.open(t, 'rb') as clip:
                        await f.write(await clip.read())
                    os.remove(t)

    async def _download_clip(self,
                             session: ClientSession,
                             folder: str,
                             headers: dict = {},
                             target: str = None) -> None:
        """下载视频片段

        @param session: 访问网络的会话管理器
        @param folder: 存储路径
        @param headers: 请求头，要求服务器返回切片数据
        @param suffix: 切片存储路径
        """
        if target is None:
            target = self.target

        # 进度条起始信息
        async with self.sema:
            async with session.get(url=self.url, headers=headers) as r:
                async with aiofiles.open(target, 'wb') as f:
                    async for chunk in r.content.iter_chunked(self.chunk_size):
                        await f.write(chunk)

                        # 进度条相关配置
                        self.current_size += self.chunk_size
                        progress = int(self.current_size / self.size * 100)
                        print(
                            '\r',
                            f'{self.name[-20:]}: ',
                            f'{self.current_size / 1024 / 1024:6.2f}',
                            '/',
                            f'{self.size / 1024 / 1024:6.2f}MB',
                            f'({progress:3}%)|',
                            'x' * progress, '.' * (100 - progress),
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
        tasks = [
            asyncio.create_task(item.download(session, folder))
            for item in self
        ]
        await asyncio.wait(tasks)

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
        print(f'\n正在将资源列表当中的内容合并到 {target} ...')

        # 拼接调用ffmpeg的系统命令
        cmd = ['ffmpeg']
        for item in self:
            cmd += ['-i', item.target]
        cmd += ['-codec', 'copy', target, '-y']

        # 调用系统ffmpeg完成视频拼接
        subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )

        # 删除临时文件
        for item in self:
            os.remove(item.target)
