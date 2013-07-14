import collections

from collections import namedtuple
from operator import attrgetter

import gdata
import gdata.youtube
import gdata.youtube.service

from youtube_dl import YoutubeDL

from six.moves import map, filter

from pprint import pprint

YouTubeService = gdata.youtube.service.YouTubeService
YouTubeVideoQuery = gdata.youtube.service.YouTubeVideoQuery


FIELDS_MAP = {
    'date': 'published.text',
    'description': 'media.description.text',
    'duration': 'media.duration.seconds',
    'title': 'media.title.text',
    'url': 'media.player.url'
}

FIELDS = list(FIELDS_MAP.iterkeys())
Video = namedtuple('video', FIELDS)


def noop(*args, **kwargs):
    pass


def extract(url):
    extractor = Extractor({'outtmpl': '', 'format_limit': '35'})
    return extractor.extract(url)


class Extractor(YoutubeDL):
    def __init__(self, params):
        super(Extractor, self).__init__(params)
        self.add_default_info_extractors()

    def extract(self, uri):
        extracted = self.extract_info(uri, download=False)
        if 'entries' not in extracted:
            return None

        entry, = extracted['entries']
        return entry

    def trouble(self, message=None, tb=None):
        pass  # TODO: should we just pass here?

    def to_screen(self, message, skip_eol=False):
        pass

    def to_stderr(self, message):
        pass


def entry2video(entry):
    fields = {name: attrgetter(attr)(entry) for (name, attr) in FIELDS_MAP.iteritems()}
    return Video(**fields)


def search(terms):
    query = YouTubeVideoQuery()
    query.vq = terms
    query.racy = 'include'
    return map(entry2video, YouTubeService().YouTubeQuery(query).entry)
