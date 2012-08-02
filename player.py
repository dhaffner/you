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
            ' ': self.pause,
            '+': functools.partial(self.seek, 1000),
            '-': functools.partial(self.seek, -1000),
            'i': self.info,
            'q': self.quit,
            '/': self.window.focus
        }

        attach = self.player.event_manager().event_attach
        getevent = functools.partial(getattr, vlc.EventType)

        def bind(event, callback, *args):
            attach(getevent(event), callback, *args)

        self.bind = bind

    def end_callback(self, event, video=None):
        self.player.stop()

    def time_callback(self, event, video):
        if not self.window:
            return
        timef = _time_format(self.player.get_time() / 1000)
        self.window.set_footer('{} {}'.format(timef, video.title))

    def info(self):
        pass

    def seek(self, delta):
        self.player.set_time(self.player.get_time() + delta)

    def play(self, video, uri):
        self.player.set_media(self.instance.media_new(uri))
        self.bind('MediaPlayerEndReached', self.end_callback, video)
        self.bind('MediaPlayerTimeChanged', self.time_callback, video)
        self.player.play()

    def pause(self):
        pass

    def input(self, video, size, key):
        if key in self.keybindings:
            apply(self.keybindings[key])
        else:
            return key

    def quit(self):
        pass
