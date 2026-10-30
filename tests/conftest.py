"""Fixtures compartilhadas para os testes."""

import numpy as np
import pytest


@pytest.fixture
def binary_labels():
    return np.array([0, 0, 1, 1])


@pytest.fixture
def ordinal_labels():
    return np.array([0, 1, 2, 3, 4])
