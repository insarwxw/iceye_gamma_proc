#!/usr/bin/env python
import numpy as np
from scipy.signal import medfilt


def median_filter_off(off, size=9, thre=3):
    # return location of filtered value (mask)

    vram = medfilt(off.real, size)
    vazm = medfilt(off.imag, size)

    mask = (np.abs(off.real - vram) > thre) | (
                np.abs(off.imag - vazm) > thre) | (off.imag == 0) | (
                       off.real == 0)

    return mask
