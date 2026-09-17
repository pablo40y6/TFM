"""Deterministic, smooth profiles used only for numerical regression tests."""

import numpy as np


def legacy_column():
    z = np.arange(50.0, 151.0, 1.0)
    total = 2.5e19 * np.exp(-z / 7.0)
    o2 = 0.21 * total
    n2 = 0.78 * total
    o = 1.0e8 + 4.0e11 * np.exp(-((z - 96.0) / 17.0) ** 2)
    o3 = 1.0e6 + 2.0e8 * np.exp(-((z - 73.0) / 10.0) ** 2)
    temperature = 185.0 + 0.018 * (z - 82.0) ** 2
    return z, o, o2, o3, n2, temperature

