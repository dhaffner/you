#!/usr/bin/env python
from __future__ import print_function

import argparse

from player import Player
from search import search, extract
from window import Window

from pprint import pprint
from six.moves import map, filter


class You(object):
    def __init__(self, no_window=True):
        self.player = None
        self.no_window = no_window

        if not no_window:
            self.window = Window(input_callback=self.on_input,
                                 select_callback=self.on_select)

    def search(self, query):
        results = search(query)
        if not self.no_window:
            self.window.set_results(results)

        for i, v in enumerate(results):
            if i > 0:
                print()

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

    def play(self, uri):
        if not self.player:
            self.player = Player()

        self.player.play(uri)

    def extract(self, url):
        return extract(url)

    def run(self):
        self.window.run()

