"""Spider for pornhub.com"""
from video_dl.extractor import Extractor
from video_dl.spider import Spider
from video_dl.toolbox import info
from video_dl.video import Media


class PornhubSpider(Spider):
    """spider for pornhub.com"""
    site = 'pornhub.com'
    home_url = 'https://www.pornhub.com'

    async def before_download(self) -> None:
        await self.parse_html(self.url)

    async def parse_html(self, target_url: str) -> None:
        """extract key information from html source code.

        Args:
            target_url: target url copied from online vide website.
        """
        info('url', target_url)
        resp, _ = await self.fetch_html(target_url)
        extractor = Extractor.create(target_url)

        video = self.create_video()
        video.title = extractor.get_title(resp)

        if self.lists:
            info('list', 'not implemented yet!')

        mp4_url = extractor.get_mp4_video_url(resp)
        mp4_dict = await self.fetch_json(mp4_url)

        for mp4 in mp4_dict:
            quality = mp4['quality']
            video.add_media(Media(**{
                'url': mp4['videoUrl'],
                'size': int(quality),
                'desc': f'{quality}P',
            }))

        self.video_list.append(video)
