import aiohttp
import asyncio
import contextvars
import math
import os
import subprocess

from prettytable import PrettyTable

from toolbox import CONFIG


client_session = contextvars.ContextVar('Aiohttp.ClientSession')
semaphore = contextvars.ContextVar('asyncio.Semaphore')


class Media(object):
    """音视频资源类"""
    chunk_size = CONFIG.chunk_size

    # 文件大小超过阈值做分段下载
    threshold = CONFIG.big_file_threshold

    def __init__(self, *,
                 url: str,
                 name: str,
                 size: float,
                 folder: str,
                 salt: str = '',
                 suffix: str = 'mp4',
                 desc: str = 'null'):
        """初始化音视频资源对象

        @param url: 在线访问网址
        @param name: 不含后缀的文件名
        @param size: 文件大小
        @param folder: 存储文件夹
        @param salt: 自定义的额外标识符
        @param suffix: 文件名后缀，默认为mp4
        @param description: 描述文本，默认为null
        """
        self.url = url
        self.name = name
        self.size = size
        self.folder = folder
        self.salt = salt
        self.suffix = suffix
        self.desc = desc

        self.target = self._get_target()

        # 当前已下载大小
        self.current_size = 0

    def _get_target(self, index: int = None) -> str:
        """获取当前资源的目标存储路径

        @param index: 资源碎片编号
        """
        # 文件名如果加盐，就添加一个下划线隔开
        salt = f'_{self.salt}' if self.salt else ''

        if index is None:
            # 默认直接返回文件名
            return os.path.join(self.folder,
                                f'{self.name}{salt}.{self.suffix}')
        else:
            # 如果提供了序号便返回碎片名
            return os.path.join(self.folder,
                                f'{self.name}{salt}_p_{index}.{self.suffix}')

    async def _get_file_size(self) -> int:
        """通过发送head请求获取目标文件大小"""
        # 从上下文管理器当中取出会话管理器
        session = client_session.get()

        headers = {'range': 'bytes=0-1'}
        async with session.get(url=self.url, headers=headers) as r:
            self.size = int(r.headers['Content-Range'].split('/')[1])

        return self.size

    def _get_headers(self,
                     total_size: int,
                     slice_size: int,
                     index: int = None) -> dict:
        """返回下载视频切片时应带上的请求头"""
        if index is None:
            return {}

        for i, v in enumerate(range(0, total_size, slice_size), 1):
            end_point = min(v + slice_size - 1, total_size - 1)
            if i == index:
                return {'range': f'bytes={v}-{end_point}'}

    async def download(self) -> None:
        """下载音视频资源到存储路径"""
        salt = f'_{self.salt}' if self.salt else ''
        print(f'正在将 {self.name[-20:]}{salt} 下载到 {self.folder} ...')

        # 获取文件大小
        size = await self._get_file_size()

        if size <= self.threshold:
            await self._download_slice()
        else:
            # 切片数目
            slice_count = math.ceil(size / self.threshold)
            tasks = [
                asyncio.create_task(self._download_slice(index))
                for index in range(1, slice_count + 1)
            ]
            await asyncio.wait(tasks)

            # 合并音视频文件碎片
            with open(self.target, 'wb') as f:
                for index in range(1, slice_count):
                    target = self._get_target(index)
                    with open(target, 'rb') as media_slice:
                        f.write(media_slice.read())
                    os.remove(target)

    async def _download_slice(self, index: int = None) -> None:
        """下载资源片段

        @param index: 当前欲下载资源切片的编号
        """
        # 从上下文管理器当中取出会话管理器
        session = client_session.get()

        # 当前欲下载资源切片的存储路径
        target = self._get_target(index)

        # 发送请求时应带上的请求头
        headers = self._get_headers(self.size, self.threshold, index)

        # 进度条起始信息
        async with semaphore.get():
            async with session.get(url=self.url, headers=headers) as r:
                with open(target, 'wb') as f:
                    async for chunk in r.content.iter_chunked(self.chunk_size):
                        f.write(chunk)

                        self.current_size += self.chunk_size
                        progress = int(self.current_size / self.size * 50)
                        print(
                            '\r',
                            f'{self.target[-20:]}: ',
                            f'{self.current_size / 1024 / 1024:6.2f}',
                            '/',
                            f'{self.size / 1024 / 1024:6.2f}MB',
                            f'({progress * 2:3}%)|',
                            'x' * progress, '.' * (50 - progress),
                            sep='', end=''
                        )


class MediaCollection(list):
    """音视频资源列表类"""
    def __init__(self, members: list = []):
        super().__init__(members)

    async def download(self, session: aiohttp.ClientSession) -> None:
        """下载资源列表当中的所有资源

        @param session: 用于访问互联网的会话管理器
        """
        # 将会话管理器传递给上下文管理器
        client_session.set(session)

        # 控制信号量
        semaphore.set(asyncio.Semaphore(CONFIG.max_conn))

        # 下载资源列表当中的所有资源
        tasks = [asyncio.create_task(item.download()) for item in self]
        await asyncio.wait(tasks)

    def __str__(self):
        """用更加漂亮的方式打印资源列表"""
        tb = PrettyTable()
        tb.field_names = ['index', 'name', 'desc', 'size', 'url']
        for index, media in enumerate(self, 1):
            tb.add_row([
                index, media.name[-20:], media.desc, media.size, media.url[:40]
            ])

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

    # TODO: 对音视频资源列表排序，因为脚本默认下载第一个资源
    def todo_sorted(self):
        pass
