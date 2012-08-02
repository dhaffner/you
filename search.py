import itertools
import collections
import operator

import gdata
import gdata.youtube
import gdata.youtube.service

from youtube_dl import FileDownloader
from youtube_dl.InfoExtractors import (YoutubePlaylistIE, YoutubeChannelIE,
                                       YoutubeSearchIE, YoutubeUserIE, YoutubeIE)

from dhaffner import misc

YouTubeService = gdata.youtube.service.YouTubeService
YouTubeVideoQuery = gdata.youtube.service.YouTubeVideoQuery

FIELDS = ('title', 'description', 'url', 'date', 'duration')
video = collections.namedtuple('video', FIELDS)

# Motivation: provide a simple FileDownloader to effectively get URLs for the
# YouTube videos we want to play.
class DummyFileDownloader(FileDownloader):
    def __init__(self, params):
        self.info_callback = misc.noop
        super(DummyFileDownloader, self).__init__(params)

    def process_info(self, info_dict):
        self.info_callback(info_dict)

    def set_info_callback(self, callback):
        self.info_callback = callback

    def to_screen(self, message, skip_eol=False):
        pass

    def to_stderr(self, message):
        pass

    def to_cons_title(self, message):
        pass

    def trouble(self, message=None, tb=None):
        pass  # TODO: should we just pass here?


def _extractors():
    return (YoutubePlaylistIE(),
            YoutubeChannelIE(),
            YoutubeUserIE(),
            YoutubeSearchIE(),
            YoutubeIE())


def _downloader():
    d = DummyFileDownloader({'outtmpl': '', 'format_limit': '35'})
    for e in _extractors():
        d.add_info_extractor(e)
    return d


#
#
#


def create_video(entry):
    getter = lambda name, attr: (name, operator.attrgetter(attr))
    fields = itertools.starmap(getter,
        [('title', 'media.title.text'),
         ('date', 'published.text'),
         ('description', 'media.description.text'),
         ('duration', 'media.duration.seconds'),
         ('url', 'media.player.url')])
    return video(**dict((name, attr(entry)) for (name, attr) in fields))


def search(terms):
    service = YouTubeService()
    query = YouTubeVideoQuery()
    query.vq = terms
    query.racy = 'include'
    entries = service.YouTubeQuery(query).entry
    return map(create_video, entries)


def extract(url, callback=None):
    downloader = _downloader()
    downloader.set_info_callback(callback)
    downloader.download([url])
