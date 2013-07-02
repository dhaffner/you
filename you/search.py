import itertools
import collections
import operator

import gdata
import gdata.youtube
import gdata.youtube.service

from youtube_dl import FileDownloader, YoutubeDL

from pprint import pprint

YouTubeService = gdata.youtube.service.YouTubeService
YouTubeVideoQuery = gdata.youtube.service.YouTubeVideoQuery

FIELDS = ('title', 'description', 'url', 'date', 'duration')
video = collections.namedtuple('video', FIELDS)


def noop(*args, **kwargs):
    pass


def extract(url, callback=None):
    extractor = Extractor({'outtmpl': '', 'format_limit': '35'})
    extractor.extract(url, callback)


# Motivation: provide a simple FileDownloader to effectively get URLs for the
# YouTube videos we want to play.
class Extractor(YoutubeDL):
    def __init__(self, params):
        super(Extractor, self).__init__(params)
        # for extractor in map(apply, EXTRACTORS):
        #     self.add_info_extractor(extractor)
        self.add_default_info_extractors()

    def extract(self, uri, callback=None):
        extracted = self.extract_info(uri, download=False)

        if 'entries' not in extracted:
            return None

        entry, = extracted['entries']
        if callback:
            callback(entry)

    def trouble(self, message=None, tb=None):
        pass  # TODO: should we just pass here?

    def to_screen(self, message, skip_eol=False):
        pass

    def to_stderr(self, message):
        pass


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


