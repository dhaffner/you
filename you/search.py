
from collections import namedtuple
from operator import attrgetter

import gdata
import gdata.youtube
import gdata.youtube.service

from six.moves import map

from subprocess import check_output


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
    cmd = ['youtube-dl', '-f', 'worst', '-g', url]
    return check_output(cmd).strip()


def entry2video(entry):
    fields = {name: attrgetter(attr)(entry)
              for (name, attr) in FIELDS_MAP.iteritems()}
    return Video(**fields)


def search(terms):
    query = YouTubeVideoQuery()
    query.vq = terms
    query.racy = 'include'
    return map(entry2video, YouTubeService().YouTubeQuery(query).entry)
