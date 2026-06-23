# coding=utf-8
"""Tests of metadata"""

import importlib
import revalidate


def test_version():
    assert revalidate.__version__ == importlib.metadata.version("revalidate")
