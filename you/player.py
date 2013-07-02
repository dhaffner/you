from __future__ import division
import sys
import time


import datetime
import functools
import re

import vlc

VLC_FLAGS = ['--no-video', '--quiet']

VLC_REMOTE = ('http://git.videolan.org/?p=vlc/bindings/python.git;a=blob_plain'
              ';f=generated/vlc.py;hb=HEAD')


def _vlc_instance(options=VLC_FLAGS):
    return vlc.Instance(options)


def _time_format(duration):
    display = str(datetime.timedelta(seconds=int(duration)))
    return re.sub(r'^(0\:)*', '', display)


class Player(object):
    def __init__(self, instance=None, window=None):
        if instance is None:
            instance = _vlc_instance()

        self.instance = instance
        self.window = window

        self.player = instance.media_player_new()
        self.keybindings = {
            'p': self.pause,
            ' ': self.pause,
            '+': functools.partial(self.seek, 1000),
            '-': functools.partial(self.seek, -1000),
            'i': self.info,
            'q': self.quit,
#            '/': self.window.focus
        }

        attach = self.player.event_manager().event_attach
        getevent = functools.partial(getattr, vlc.EventType)

        def bind(event, callback, *args):
            attach(getevent(event), callback, *args)

        self.bind = bind

    def end_callback(self, event, video=None):
        self.player.stop()
        #self.window.feedback('{} {}'.format(timef, video.title))

    def info(self):
        pass

    def seek(self, delta):
        self.player.set_time(self.player.get_time() + delta)

    def play(self, uri):
        self.player.set_media(self.instance.media_new(uri))
        # self.bind('MediaPlayerEndReached', self.end_callback, video)

        progress = Progress(self.player.get_length())

        def time_changed(event):
            current = self.player.get_time()
            progress.update(current)

        def length_changed(event):

            low, high = 0, self.player.get_length()
            progress.extents(low, high)

        self.bind('MediaPlayerLengthChanged', length_changed)
        self.bind('MediaPlayerTimeChanged', time_changed)

        self.player.play()
        while True:
            continue

    def pause(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def input(self, video, size, key):
        if key in self.keybindings:
            apply(self.keybindings[key])
        else:
            return key

    def quit(self):
        pass


class Progress(object):
    def __init__(self, low=0, high=0):
        self.extents(low, high)

    def start(self):
        self.update(self.low)

    def finish(self):
        self.update(self.high)

    def update(self, value):
        percent = ((value - self.low) / self.high) * 100

        sys.stdout.write("\r|%-73s| %d%%" % ('#' * int(percent * .73), percent))
        sys.stdout.flush()

    def extents(self, low, high):
        self.low, self.high = low, high
