"""Spider for xvideos.com"""
from video_dl.extractor import Extractor
from video_dl.spider import Spider
from video_dl.toolbox import info
from video_dl.video import Media


class XVideosSpider(Spider):
    """spider for xvideos.com"""
    site = 'xvideos.com'
    home_url = 'https://www.xvideos.com/'

    async def before_download(self) -> None:
        info('url', self.url)

        target_url = self.url
        resp, _ = await self.fetch_html(target_url)
        extractor = Extractor.create(target_url)

        video = self.create_video()
        video.title = extractor.get_title(resp)

        for mp4 in extractor.get_mp4_video(resp):
            video.add_media(Media(**mp4))
        self.video_list.append(video)

        if self.lists:
            info('list', 'not implemented yet!')
