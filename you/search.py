from collections import namedtuple
from operator import attrgetter

from gdata.youtube.service import YouTubeService, YouTubeVideoQuery

FIELD_MAP = {
    'date': 'published.text',
    'description': 'media.description.text',
    'duration': 'media.duration.seconds',
    'title': 'media.title.text',
    'url': 'media.player.url'
}


Video = namedtuple('video', FIELD_MAP.keys())


def entry2video(entry):
    fields = {name: attrgetter(attr)(entry)
              for (name, attr) in FIELD_MAP.items()}
    return Video(**fields)


def youtube_search(terms):
    query = YouTubeVideoQuery()
    query.vq = terms
    query.racy = 'include'
    return (entry2video(e) for e in YouTubeService().YouTubeQuery(query).entry)
