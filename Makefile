.PHONY: install vlc.py

all: install

install: vlc.py
	python setup.py install

vlc.py:
	curl -o ./you/vlc.py "http://git.videolan.org/?p=vlc/bindings/python.git;a=blob_plain;f=generated/vlc.py;hb=HEAD"
