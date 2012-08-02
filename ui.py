#!/usr/bin/env python
from __future__ import print_function
import urwid


PALETTE = [('prompt focus', 'light cyan', 'default'),
           ('prompt', 'default', 'default'),
           ('reveal focus', 'light cyan', 'default', 'bold')]


class SearchResultBox(urwid.ListBox):
    def render(self, size, **kw):
        cols, rows = size
        return super(SearchResultBox, self).render(size, **kw)


class SearchResultWalker(urwid.SimpleListWalker):
     # def __init__(self, ui, *args, **kw):
     #   super(LineWalker, self).__init__(*args, **kw)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


class SearchResult(urwid.WidgetWrap):  # Manage individual lines. (rows)

    def __init__(self, video, callback=None):
        self.video = video
        self.callback = callback
        self.title = urwid.Text(video.title, wrap='clip')
        self.description = urwid.Text((video.description or '').strip(),
                                      wrap='clip')

        self.item = [self._title(self.title),
                     self._description(self.description)]

        w = self.columns = urwid.Columns(self.item, dividechars=1)
        self.__super.__init__(w)

    def _title(self, text):
        return urwid.Padding(urwid.AttrWrap(text, 'body', 'reveal focus'),
                             left=2, right=2)

    def _description(self, text):
        return urwid.AttrWrap(text, 'body', 'focus')

    def selectable(self):
        return True

    def keypress(self, size, key):
        if self.callback is not None:
            return self.callback(self.video, size, key)
        return key


class ui(object):
    def __init__(self, walker=None, content=None):
        if content is None:
            content = []
        if walker is None:
            walker = SearchResultWalker(content)
        box = SearchResultBox(walker)

        self.footer = urwid.Text('', wrap='clip')
        frame = urwid.Frame(box, footer=self.footer)

        self.box = box
        self.frame = frame
        self.walker = walker

        self.content = content

        self.loop = urwid.MainLoop(frame, PALETTE, unhandled_input=self.input)

    def input(self, *args, **kwargs):
        pass

    def run(self):
        self.loop.run()

    def transform(self, videos, callback=None):
        return (SearchResult(v, callback) for v in videos)

#     box = SearchResultBox
# if walker is None:
#     walker = SearchResultWalker
# return
