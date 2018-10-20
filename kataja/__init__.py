# coding=utf-8
import os

name = 'kataja'
parent = os.path.dirname(os.path.dirname(__file__))

try:
    with open(os.path.join(parent, 'VERSION')) as version_file:
        __version__ = version_file.read().rsplit('|', 1)[-1].strip()
except FileNotFoundError:
    import pkg_resources
    __version__ = pkg_resources.get_distribution('kataja').version
