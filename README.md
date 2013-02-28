An audio-only YouTube player for the command line.

Usage
=====

Search for a video on YouTube

    ./you.py "dirt off your shoulder"

    ./you.py men at work land down under


Display the help.

    ./you.py -h

*Keyboard controls*

Esc - quit

Tab - switch between input and result list

Enter - search or play selected result

Install
=======

The requirements for this are urwid, GData, youtube-dl, and the VLC Python bindings. The former three are installable via pip. Here are installation instructions:

    git clone https://github.com/dhaffner/you.git
    cd you
    make
