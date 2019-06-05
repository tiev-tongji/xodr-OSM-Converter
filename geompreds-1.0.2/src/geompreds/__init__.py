"""A Python wrapper for 2D predicates of Jonathan Richard Shewchuk
"""

__version__ = '1.0.2'
__license__ = 'MIT License'
__author__ = 'Martijn Meijers'
__creation_date__ = '2010-02-26'

from ._geompreds import orient2d, incircle

__all__ = ["orient2d", "incircle"]
