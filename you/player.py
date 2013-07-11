from __future__ import division

import time
import datetime
import functools
import re

from you import vlc
from you.helpers import Progress


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
            'q': self.quit,
#            '/': self.window.focus
        }

        attach = self.player.event_manager().event_attach
        getevent = functools.partial(getattr, vlc.EventType)

        def bind(event, callback, *args):
            attach(getevent(event), callback, *args)
        self.bind = bind

    def seek(self, delta):
        self.player.set_time(self.player.get_time() + delta)

    def play(self, uri):
        player = self.player
        player.set_media(self.instance.media_new(uri))

        progress = Progress()

        def time_changed(event):
            progress.update(player.get_time())

        def length_changed(event):
            progress.extents(0, player.get_length())

        def play_end(event=None):
            progress.clear()

        self.bind('MediaPlayerLengthChanged', length_changed)
        self.bind('MediaPlayerTimeChanged', time_changed)
        self.bind('MediaPlayerEndReached', play_end)

        player.play()

        try:

            # Sleep until the media begins playing.
            while True:
                if player.is_playing():
                    break
                time.sleep(1.0)

            while True:
                remaining = player.get_length() - player.get_time()  # ms
                if remaining <= 0:
                    break
                time.sleep(min(1.0, remaining * 1000))

        except KeyboardInterrupt:
            play_end()

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
