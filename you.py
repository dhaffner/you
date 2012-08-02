#!/usr/bin/env python

import collections
import datetime
import functools
import gdata
import gdata.youtube
import gdata.youtube.service
import itertools
import operator
import pprint
import urwid
import re
import sys



import concurrent.futures
import vlc

import extract

from youtube_dl.InfoExtractors import YoutubeIE

from dhaffner import misc, functions, sequences

from ui import ui


DEBUG = pprint.pprint
FIELDS = ('title', 'description', 'url', 'date', 'duration')
VLC = ('--no-video', '--intf=dummy')

video = collections.namedtuple('video', FIELDS)


YouTubeService = functions.memoize(gdata.youtube.service.YouTubeService)
YouTubeVideoQuery = gdata.youtube.service.YouTubeVideoQuery


#
# Helper functions
#


def _instance(options=VLC):
    return vlc.Instance(options)


def _player(instance=None):
    if instance is None:
        return vlc.MediaPlayer()
    else:
        return instance.media_player_new()


def _video(entry):

    getter = lambda name, attr: (name, operator.attrgetter(attr))

    fields = itertools.starmap(getter,
    (('title', 'media.title.text'),
     ('date', 'published.text'),
     ('description', 'media.description.text'),
     ('duration', 'media.duration.seconds'),
     ('url', 'media.player.url')
    ))

    return video(**dict((name, attr(entry)) for (name, attr) in fields))


def _timef(duration):
    display = str(datetime.timedelta(seconds=int(duration)))
    return re.sub(r'^(0\:)*', '', display)


def _search(terms):
    service = YouTubeService()
    query = YouTubeVideoQuery()
    query.vq = terms
    query.racy = 'include'
    entries = service.YouTubeQuery(query).entry
    return itertools.imap(_video, entries)


def _play(_player, _instance, video, size, key):
    if key == "enter":

        DEBUG('extracting {}'.format(video.url))
        urls = extract.extract(video.url)
        if not len(urls):
            return key


        uri = sequences.first(urls)['url']

        DEBUG('attemping to play {}'.format(uri))

        m = _instance.media_new(uri)
        _player.set_media(m)
        _player.play()

        DEBUG('streaming "{}"'.format(video.title))

    elif key == 'Q':
        raise urwid.ExitMainLoop()
    return key


if __name__ == '__main__':
    terms = ' '.join(sys.argv[1:])
    #main(sys.argv[1:])
    if len(terms) == 0:
        exit()
    else:
        instance = _instance()
        player = _player(instance)
        play = functools.partial(_play, player, instance)
        main = ui()

        results = _search(terms)
        results = main.transform(results, callback=play)
        main.walker.extend(results)

        DEBUG = main.footer.set_text

        main.run()