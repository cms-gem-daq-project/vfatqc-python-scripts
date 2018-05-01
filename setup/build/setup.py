#!/usr/bin/env python

# Thanks to https://github.com/softwarefactory-project/rdopkg/blob/master/setup.py

import re
import setuptools
import sys

try:
    import multiprocessing  # noqa
except ImportError:
    pass

setuptools.setup(
    setup_requires=['pbr'],
    pbr=True,
)
