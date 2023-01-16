# -*- coding: utf-8 -*-
##############################################
# The MIT License (MIT)
# Copyright (c) 2014 Kevin Walchko
# see LICENSE for full details
##############################################
from importlib.metadata import version

from squaternion.squaternion import Quaternion

__author__ = "Kevin Walchko"
__license__ = "MIT"
__version__ = version("squaternion")

__all__ = [
    'Quaternion',
]
