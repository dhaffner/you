# you

An audio-only YouTube player for the command line.

## Requirements

you relies on [VLC](http://www.videolan.org/) being installed already. All other dependencies should be installed automatically as needed.

## Installation

you is installable via pip.

    pip install https://github.com/dhaffner/you.git

After that, type `you` to verify that the install completed successfully.

## Usage

To show the full list of commandline options, run:

    you -h

#### Search for a video on YouTube

    you -q will smith summertime

#### Play a specific video URL

    you --url="http://www.youtube.com/watch?v=S6WpvBHdk1c"

#### Play a video by specifying its ID

    you -v S6WpvBHdk1c

#### Search for a video and play the first result

    you -l will smith summertime

## Keyboard shortcuts

`p` or ` `: pause

`CTRL-c`: quit

`-`, `+`: seek backward or forward 1 second
