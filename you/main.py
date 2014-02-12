#!/usr/bin/env python
from __future__ import print_function

from you.helpers import lazyproperty, get_full_line, take
from you.player import Player
from you.search import search, extract


class You(object):
    def __init__(self):
        pass

    @lazyproperty
    def player(self):
        return Player()

    def search(self, query, limit=10, lucky=False):
        results = search(query)

        if limit and limit > 0:
            results = take(limit, results)

        if lucky:
            v = next(results)
            self.play(v.url)
            return

        hr = get_full_line()
        for i, v in enumerate(results):
            if i > 0:
                print(hr)

            print('{:02d} {}'.format(i, v.title))

            if v.description:
                print('   {}'.format(v.description))

            print('   {}'.format(v.url))

    def play(self, url):
        extracted = extract(url)
        if extracted:
            self.player.play(extracted, label='')
