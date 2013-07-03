#!/usr/bin/env python
from __future__ import print_function

import argparse

from helpers import lazyproperty, get_full_line, take

from player import Player
from search import search, extract
from window import Window

from pprint import pprint
from six.moves import map, filter

class You(object):
    def __init__(self, no_window=True):
        self.no_window = no_window

        if not no_window:
            self.window = Window(input_callback=self.on_input,
                                 select_callback=self.on_select)

    @lazyproperty
    def player(self):
        return Player()

    def search(self, query, limit=10):
        results = search(query)

        if limit and limit > 0:
            results = take(limit, results)

        if not self.no_window:
            self.window.set_results(results)

        hr = get_full_line()
        for i, v in enumerate(results):
            if i > 0:
                print(hr)

            print('{:02d} {}'.format(i, v.title))

            if v.description:
                print('   {}'.format(v.description))

            print('   {}'.format(v.url))


    def on_input(self, text):
        results = search(text)
        self.window.set_results(results)

    def on_select(self, video, size=None, key=None):
        if not (size or key):  # new video
            self.extract(video)

        elif self.player:
            self.player.input(video, size, key)

        return key

    def play(self, url):
        extracted = extract(url)
        if extracted and 'url' in extracted:
            self.player.play(extracted['url'])

    def extract(self, url):
        return extract(url)

    def run(self):
        self.window.run()
