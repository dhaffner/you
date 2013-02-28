#!/usr/bin/env python
from __future__ import print_function

import argparse

from player import Player
from search import search, extract
from window import Window


class You(object):
    def __init__(self, args):
        query = None
        if args.term:
            query = ' '.join(args.term)

        self.player = None
        self.window = window = Window(query=query,
                                      input_callback=self.on_input,
                                      select_callback=self.on_select)

    def on_input(self, text):
        results = search(text)
        self.window.set_results(results)

    def on_select(self, video, size=None, key=None):
        if not (size or key):  # new video
            self.extract(video)

        elif self.player:
            self.player.input(video, size, key)

        return key

    def play(self, video, uri):
        if not self.player:
            self.player = Player(window=self.window)
        self.player.play(video, uri)

    def extract(self, video):
        if not self.player:
            self.player = Player(window=self.window)

        def callback(info):
            if 'url' not in info:
                # TODO: fuck
                return
            self.play(video, info['url'])
        self.window.feedback('--:-- trying to extract video URL for {}'.format(video.title))
        extract(video.url, callback=callback)

    def run(self):
        self.window.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A videoless command-line YouTube player.')

    parser.add_argument('--config', nargs='?', dest='config', metavar='filename',
                        help='configuration file (currently not implemented)')
    parser.add_argument('term', nargs='*',
                        help='term(s) to search for')

    args = parser.parse_args()

    main = You(args)
    main.run()
