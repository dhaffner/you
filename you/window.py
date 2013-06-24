#!/usr/bin/env python
from __future__ import print_function

import urwid
from urwid import curses_display


PALETTE = [('prompt focus', 'light cyan', 'default'),
           ('prompt', 'default', 'default'),
           ('reveal focus', 'light cyan', 'default', 'bold')]


def noop(*args, **kwargs):
    pass


class SearchEdit(urwid.Edit):
    def __init__(self, callback=None, caption='~ ', main=None, *args, **kwargs):
        super(SearchEdit, self).__init__(caption=caption, *args, **kwargs)

    def keypress(self, size, key):
        if len(key) > 1 and key not in ('backspace', ):
            return key

        else:
            return super(SearchEdit, self).keypress(size, key)

        return key

    def clear(self):
        self.set_edit_text('')


class SearchResultBox(urwid.ListBox):
    pass


class SearchResultWalker(urwid.SimpleListWalker):
    def selectable(self):
        return True


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
                             left=0, right=1)

    def _description(self, text):
        return urwid.AttrWrap(text, 'body', 'focus')

    def selectable(self):
        return True

    def keypress(self, size, key):
        if self.callback:
            return self.callback(self.video, size, key)
        return key


class Window(object):
    def __init__(self, **kwargs):
        self.content = []

        self.walker = SearchResultWalker(self.content)
        box = SearchResultBox(self.walker)

        self.input = SearchEdit(edit_text="", main=self)

        self.header = urwid.AttrWrap(self.input, 'prompt', 'prompt focus')
        self.footer = urwid.Text('', wrap='clip')
        frame = urwid.Frame(body=box, header=self.header, footer=self.footer,
                            focus_part='header')

        self.box = box
        self.frame = frame
        self.loop = urwid.MainLoop(frame, PALETTE,
                                   handle_mouse=False,
                                   screen=curses_display.Screen(),
                                   unhandled_input=self.unhandled)

        # Handle kwargs

        self.input_callback = kwargs.get('input_callback', noop)
        self.select_callback = kwargs.get('select_callback', noop)
        self.query = kwargs.get('query', '')

    def unhandled(self, key):
        focused = self.frame.focus_position

        if key in ('enter', ):
            if focused == 'header':
                self.input_callback(self.input.get_edit_text())
            elif focused == 'body':
                selected, _ = self.walker.get_focus()
                self.select_callback(selected.video)

        if key == 'tab':
            if focused == 'header':
                self.focus('body')
            else:
                self.focus('header')
                self.input.clear()

        if key == 'down' and focused == 'header':
            self.focus('body')

        if key in ('Q', 'esc'):
            self.quit()
        return

    def run(self):
        if self.query:
            self.input.set_edit_text(self.query)
            self.input_callback(self.query)
            del self.query
        self.loop.run()

    def refresh(self):
        self.loop.draw_screen()

    def quit(self):
        raise urwid.ExitMainLoop()

    def focus(self, part='header'):
        self.frame.set_focus(part)

    def set_footer(self, text):
        self.footer.set_text(text)
        self.refresh()

    feedback = set_footer  # Convenience alias

    def set_results(self, results):
        self.walker[:] = [SearchResult(r, callback=self.select_callback) for r in results]

    def set_input_callback(self, callback):
        self.input_callback = callback

    def set_select_callback(self, callback):
        self.select_callback = callback
