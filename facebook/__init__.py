"""
Module: facebook/__init__.py

Facebook automation package.
"""

from facebook.composer import FacebookComposer
from facebook.selectors import SELECTORS, XPATH_PREFIX

__all__ = ['FacebookComposer', 'SELECTORS', 'XPATH_PREFIX']

