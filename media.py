"""Library for handling media.

Some online video website stores their video (picture) and audio (sound)
separately in differrent place. So, if we want to download a complete video,
we should download video and audio (I say, media) first, and then merge them to
one.

when downloading a single media, if its size exceeds a certain threshold,
program will slice it to many fragment and download with different coroutine.

Available function:
    - Media().download: download a media from internet.
    - MediaCollection().download: download medias contained in MediaCollection.
    - MediaCollection().merge: combined medias contained in collection to one.

Typical usage example:
    media1 = Media(**{'url': 'url1', 'name': '1', size: '1', folder: '.'})
    media2 = Media(**{'url': 'url2', 'name': '2', size: '2', folder: '.'})
    media_collection = MediaCollation([media1, media2])
    for media in media_collection:
        media.download()
"""
import aiohttp
import asyncio
import contextvars
import math
import os
import subprocess

from prettytable import PrettyTable

from toolbox import Config


session = contextvars.ContextVar('Aiohttp.ClientSession')
semaphore = contextvars.ContextVar('asyncio.Semaphore')


class Media(object):
    """Class used to handle media."""
    _config = Config()

    chunk_size = _config.chunk_size
    threshold = _config.big_file_threshold

    def __init__(self, *, url: str, name: str, size: float, folder: str,
                 salt: str = '', suffix: str = 'mp4', desc: str = 'null'):
        """Initialize a media object.

        Args:
            url: target url.
            name: media's file name without suffix.
            size: media's file size.
            folder: folder where media will save to.
            salt: extra string will be inserted into file name.
            suffix: suffix, default: mp4.
            desc: description of media, default: null.
        """
        self.url = url
        self.name = name
        self.size = size
        self.folder = folder
        self.salt = salt
        self.suffix = suffix
        self.desc = desc

        self.target = self._get_target()

        self.current_size = 0  # file size during downloading process

    def _get_target(self, index: int = None) -> str:
        """get media slice's target storage path.

        insert a index into file name and return.

        Args:
            index: index of media slice.

        Returns:
            media slice's target storage path. e.g.: media_p_2.mp4.
        """
        salt = f'_{self.salt}' if self.salt else ''

        if index is None:
            return os.path.join(self.folder,
                                f'{self.name}{salt}.{self.suffix}')
        else:
            return os.path.join(self.folder,
                                f'{self.name}{salt}_p_{index}.{self.suffix}')

    async def _set_size(self) -> None:
        """set media file's real size by parsing server's response headers."""
        headers = {'range': 'bytes=0-1'}
        async with session.get().get(url=self.url, headers=headers) as r:
            self.size = int(r.headers['Content-Range'].split('/')[1])

    def _get_headers(self, index: int = None) -> dict:
        """get a header should be sent to server for downloading a media slice.

        Args:
            index: index of media slice. begin with 1.

        Returns:
            a request header with slice range. defalut: {}.
        """
        if index is None:
            return {}

        slice_point = range(0, self.size, self.threshold)
        start_point = slice_point[index - 1]
        end_point = min(start_point + self.threshold - 1, self.size - 1)
        return {'range': f'bytes={start_point}-{end_point}'}

    async def download(self) -> None:
        """download media to target folder."""
        print(f'正在将 {self.target[-20:]} 下载到 {self.folder} ...')

        await self._set_size()
        if self.size <= self.threshold:  # don't need silce
            await self._download_slice()
        else:
            slice_count = math.ceil(self.size / self.threshold)

            # create task and run
            await asyncio.wait([
                asyncio.create_task(self._download_slice(index))
                for index in range(1, slice_count + 1)
            ])

            # merge media slices to a complete one
            # and remove these media slices
            with open(self.target, 'wb') as f:
                for index in range(1, slice_count):
                    target = self._get_target(index)
                    with open(target, 'rb') as media_slice:
                        f.write(media_slice.read())
                    os.remove(target)

    async def _download_slice(self, index: int = None) -> None:
        """download media slice from internet

        @param index: index of media slice which we want to download.
        """
        target = self._get_target(index)  # get target location to save media
        headers = self._get_headers(index)  # get headers to send to server

        async with semaphore.get():
            async with session.get().get(url=self.url, headers=headers) as r:
                with open(target, 'wb') as f:
                    async for chunk in r.content.iter_chunked(self.chunk_size):
                        f.write(chunk)

                        # a naive progress bar
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
    """class for handle list of medias."""
    _config = Config()

    def __init__(self, members: list = None):
        if members is None:
            members = []
        super().__init__(members)

    async def download(self, client_session: aiohttp.ClientSession) -> None:
        """download all medias contained in this collection.

        Args:
            client_session: a session used to connect internet.
        """
        session.set(client_session)
        semaphore.set(asyncio.Semaphore(self._config.max_conn))

        # download all media
        await asyncio.wait([
            asyncio.create_task(item.download()) for item in self
        ])

    def __str__(self):
        """print this media collection with pretty format."""
        tb = PrettyTable()
        tb.field_names = ['index', 'name', 'desc', 'url']
        for index, media in enumerate(self, 1):
            tb.add_row([index, media.name[-20:], media.desc, media.url[:40]])
        return tb.get_string()

    def merge(self, target: str) -> None:
        """merge all medias into a complete one.

        only workable after all medias are ready.

        Args:
            target: target location to save video.
        """
        print(f'\n正在将资源列表当中的内容合并到 {target} ...')

        # command line command
        cmd = ['ffmpeg']
        for item in self:
            cmd += ['-i', item.target]
        cmd += ['-codec', 'copy', target, '-y']

        # call command provided by opration system
        subprocess.run(cmd, stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT, check=True)

        # remove temporary files
        for item in self:
            os.remove(item.target)

    # TODO: sort items in MediaCollection,
    # because we download the first item in list by default.
    def todo_sorted(self):
        pass
