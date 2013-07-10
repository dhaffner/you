from __future__ import division

import sys

from itertools import islice
from subprocess import check_output




def rprint(string, file=sys.stdout, flush=True, prepend='\r'.__add__):
    if not string.startswith('\r'):
        string = prepend(string)

    file.write(string)
    if flush:
        file.flush()


class lazyproperty(property):
    """
    A decorator for lazily-evaluated object properties.
    """
    def __init__(self, *args):
        self.__called__ = False
        super(lazyproperty, self).__init__(*args)

    def __get__(self, obj, type=None):
        if obj is None:
            return None
        elif self.__called__:
            value = self.__value__
        else:
            value = self.__value__ = self.fget(obj)
            self.__called__ = True
        return value

    def __delete__(self, obj):
        if self.__called__:
            self.__called__ = False
            del self.__value__


class Progress(object):
    def __init__(self, low=0, high=0):
        self.extents(low, high)

        self.width = 80
        try:
            self.width = get_console_width()
        except:  # TODO specify Exception
            pass

    def start(self):
        self.update(self.low)

    def finish(self):
        self.update(self.high)

    def clear(self):
        rprint('')

    def update(self, value, labels=None):
        if self.high == 0:
            return

        percent = ((value - self.low) / self.high)

        bar_length = self.width  # save padding for time display
        num_bars = int(percent * bar_length)

        if labels:
            a, b = labels
            bar_length -= (len(a) + len(b) + 2)
            num_bars = int(percent * bar_length)
            bar = '{} {}{} {}'.format(a,
                                      '#' * num_bars,
                                      ' ' * (bar_length - num_bars),
                                      b)
        else:
            bar = '{}{}'.format('#' * num_bars, ' ' * (bar_length - num_bars))

        rprint(bar)

    def extents(self, low, high):
        self.low, self.high = low, high


def get_console_width():
    output = check_output('tput cols', shell=True)
    return int(output.strip())


def get_full_line():
    w = get_console_width()
    return '-' * w


def take(n, iterable, islice=islice):
    """Take the first n elements of the given iterable."""
    return islice(iterable, n)