#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the csr2transmart module.
"""

import pytest
from csr2transmart import csr2transmart


def test_something():
    assert True


def test_with_error():
    with pytest.raises(ValueError):
        # Do something that raises a ValueError
        raise ValueError


def test_start_script():
    csr2transmart.main()
