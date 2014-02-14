from setuptools import setup

setup(name='you',
      version='0.2',
      description='An audio-only YouTube player for the command line.',
      url='http://github.com/dhaffner/you',
      author='Dustin Haffner',
      author_email='dh@xix.org',
      license='MIT',
      packages=['you'],
      scripts=['bin/you'],
      install_requires=['docopt', 'gdata', 'youtube_dl'],
      zip_safe=False)
