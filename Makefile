# See the README for installation instructions.

all: packages vlc.py

# Modify this rule to build your own custom release.

packages:
	pip install -r ./requirements.txt

vlc.py:
	curl -o vlc.py "http://git.videolan.org/?p=vlc/bindings/python.git;a=blob_plain;f=generated/vlc.py;hb=HEAD"

clean:
	rm ./vlc.py *.pyc
