import itertools
import collections
import operator

import gdata
import gdata.youtube
import gdata.youtube.service

from youtube_dl import FileDownloader
from youtube_dl.InfoExtractors import (YoutubePlaylistIE, YoutubeChannelIE,
                                       YoutubeSearchIE, YoutubeUserIE, YoutubeIE)

YouTubeService = gdata.youtube.service.YouTubeService
YouTubeVideoQuery = gdata.youtube.service.YouTubeVideoQuery

FIELDS = ('title', 'description', 'url', 'date', 'duration')
video = collections.namedtuple('video', FIELDS)


EXTRACTORS = (YoutubePlaylistIE,
              YoutubeChannelIE,
              YoutubeSearchIE,
              YoutubeUserIE,
              YoutubeIE)


def noop(*args, **kwargs):
    pass


def extract(url, callback=None):
    downloader = DummyFileDownloader({'outtmpl': '', 'format_limit': '35'})
    downloader.extract(url)


# Motivation: provide a simple FileDownloader to effectively get URLs for the
# YouTube videos we want to play.
class DummyFileDownloader(FileDownloader):
    def __init__(self, params):
        super(DummyFileDownloader, self).__init__(params)
        for extractor in map(apply, EXTRACTORS):
            self.add_info_extractor(extractor)

    def extract(self, uri):
        print self.extract_info(uri, download=False)

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


