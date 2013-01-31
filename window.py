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
        # if callback is None:
        #     callback = misc.noop

        # self.callback = callback
        # self.main = main
        super(SearchEdit, self).__init__(caption=caption, *args, **kwargs)

    def keypress(self, size, key):
        if len(key) > 1 and key not in ('backspace', ):
            return key

        else:
            return super(SearchEdit, self).keypress(size, key)

        return key
        # if key == 'enter':
        #     self.callback(self.edit_text)

        # elif key == '/':
        #     self.main.focus('body')

        # else:
        #     return super(SearchEdit, self).keypress(size, key)

    def clear(self):
        self.set_edit_text('')


class SearchResultBox(urwid.ListBox):
    # def keypress(self, size, key):
    #     return key
    pass

class SearchResultWalker(urwid.SimpleListWalker):
    def selectable(self):
        return True

    # def keypress(self, size, key):
    #     return key


class SearchResult(urwid.WidgetWrap):  # Manage individual lines. (rows)

    def __init__(self, video, callback=None):
        self.video = video
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
        # if self.callback is not None:
        #     return self.callback(self.video, size, key)
        return key


class Window(object):
    def __init__(self):
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

        self.input_callback = self.select_callback = noop

    def unhandled(self, key):
        focused = self.frame.focus_position

        if key in ('enter', ):
            if focused == 'header':
                self.input_callback(self.input.get_edit_text())
            elif focused == 'body':
                selected, _  = self.walker.get_focus()
                self.select_callback(selected.video)

        if key == 'tab':
            if focused == 'header':
                self.focus('body')
            else:
                self.focus('header')

        if key == 'down' and focused == 'header':
            self.focus('body')


        if key in ('Q', 'esc'):
            self.quit()
        return

    def run(self):
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

    def set_results(self, results):
        self.walker[:] = [SearchResult(r) for r in results]

    def set_input_callback(self, callback):
        self.input_callback = callback

    def set_select_callback(self, callback):
        self.select_callback = callback
