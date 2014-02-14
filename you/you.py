#!/usr/bin/env python
from __future__ import print_function

from .helpers import get_full_line, take
from .player import Player
from .search import youtube_search

from subprocess import check_output


def search(query, limit=-1, lucky=False):
    results = youtube_search(query)

    if limit and limit > 0:
        results = take(limit, results)

    if lucky:
        v = next(results)
        play(v)
        return

    hr = get_full_line()
    for i, v in enumerate(results):
        if i > 0:
            print(hr)

        print('{:02d} {}'.format(i, v.title))

        if v.description:
            print('   {}'.format(v.description))

        print('   {}'.format(v.url))


def extract(url):
    cmd = ['youtube-dl', '-f', 'worst', '-g', url]
    return check_output(cmd).strip()


def play(video):
    extracted = extract(video.url)
    if extracted:
        player = Player()
        player.play(extracted, label=video.title)
