from __future__ import division

import time
from datetime import timedelta
from functools import partial
import re

import sys
import select
import tty
import termios

from . import vlc
from .helpers import Progress

VLC_FLAGS = ['--no-video', '--quiet']


def _vlc_instance(options=VLC_FLAGS):
    return vlc.Instance(options)


def _check_for_input():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])


def _timef(duration):
    display = str(timedelta(seconds=int(duration)))
    return re.sub(r'^(0\:)*', '', display)


class Player(object):
    def __init__(self, instance=None):
        if instance is None:
            instance = _vlc_instance()

        self.instance = instance

        self.player = instance.media_player_new()
        self.keybindings = {
            'p': self.pause,
            ' ': self.pause,
            '+': partial(self.seek, 1000),
            '-': partial(self.seek, -1000),
            'q': self.quit,
        }

        attach = self.player.event_manager().event_attach
        getevent = partial(getattr, vlc.EventType)

        def bind(event, callback, *args):
            attach(getevent(event), callback, *args)

        self.bind = bind

    def seek(self, delta):
        self.player.set_time(self.player.get_time() + delta)

    def play(self, uri, label=None):
        player = self.player
        player.set_media(self.instance.media_new(uri))

        progress = Progress()

        def time_changed(event):
            start, end = player.get_time(), player.get_length()
            labels = (' '.join(filter(None, [label, _timef(start / 1000)])),
                      _timef(end / 1000))
            progress.update(start, labels=labels)

        def length_changed(event):
            progress.extents(0, player.get_length())

        def play_end(event=None):
            progress.clear(True)

        self.bind('MediaPlayerLengthChanged', length_changed)
        self.bind('MediaPlayerTimeChanged', time_changed)
        self.bind('MediaPlayerEndReached', play_end)

        player.play()

        settings = termios.tcgetattr(sys.stdin)
        try:

            tty.setcbreak(sys.stdin.fileno())

            # Sleep until the media begins playing.
            while True:
                if player.is_playing():
                    break
                time.sleep(1.0)

            while True:
                if _check_for_input():
                    self.input(sys.stdin.read(1))

                remaining = player.get_length() - player.get_time()  # ms
                if remaining <= 0:
                    break

                time.sleep(min(1.0, remaining * 1000))

        except KeyboardInterrupt:
            play_end()

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

    def pause(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def input(self, key):
        if key in self.keybindings:
            apply(self.keybindings[key])

    def quit(self):
        pass
