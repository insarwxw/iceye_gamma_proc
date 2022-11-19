import os
import numpy as np
from fparam import *
from median_filter_off import median_filter_off
from scipy.signal import medfilt
from congrid2d import congrid2d


def c_off4intf(id1, id2, range_spacing=None, azimuth_spacing=None, fill=False, \
               interf=None):

    # - Read Offsets Parameters
    poff = off_param()
    poff.load(id1 + '-' + id2 + '.offmap.par')
    range_spacing = poff.rgsp
    azimuth_spacing = poff.azsp
    print('Range spacing :', range_spacing)
    print('Azimuth spacing :', azimuth_spacing)

    # - Read Offsets
    off = np.fromfile(id1 + '-' + id2 + '.offmap.off',
                      dtype=np.complex64).reshape(poff.nrec,
                                                  poff.npix).byteswap()

    # - Generate Ramp
    x = np.ones([poff.nrec, 1], dtype='float32') \
        * (np.arange(poff.npix, dtype='float32').reshape([1, poff.npix]))
    y = np.ones([1, poff.npix], dtype='float32') \
        * np.arange(poff.nrec, dtype='float32').reshape([poff.nrec, 1])

    x_var = poff.x_start + x * poff.rgsp
    y_var = poff.y_start + y * poff.azsp

    ramp_offx = poff.xoff[0] + x_var * poff.xoff[1] + y_var * poff.xoff[2]

    ramp_offy = poff.yoff[0] + x_var * poff.yoff[1] + y_var * poff.yoff[2]

    # - Apply Median Filter to Offsets
    medfilt_size = 9
    medthre = 1
    mask = median_filter_off(off, size=medfilt_size, thre=medthre)

    mask[:, 0:2] = 1
    mask[:, poff.npix - 2:] = 1
    mask[0:2, :] = 1
    mask[poff.nrec - 2:, :] = 1

    xoff_masked = np.ma.array(off.real, mask=mask)
    yoff_masked = np.ma.array(off.imag, mask=mask)

    del off
    del mask

    xoff_masked.mask = xoff_masked.mask | \
                       (medfilt(xoff_masked.filled(fill_value=0), 3) == 0) | \
                       (medfilt(yoff_masked.filled(fill_value=0), 3) == 0)

    yoff_masked.mask = yoff_masked.mask | \
                       (medfilt(xoff_masked.filled(fill_value=0), 3) == 0) | \
                       (medfilt(yoff_masked.filled(fill_value=0), 3) == 0)

    xoff_masked = xoff_masked - ramp_offx
    yoff_masked = yoff_masked - ramp_offy

    # off_masked = xoff_masked.filled(0) + 1j*yoff_masked.filled(0)

    # off_masked.byteswap().tofile('test')
    # os.system('rasmph test '+str(poff.npix))

    del ramp_offx, ramp_offy  # , off_masled

    # re-interpolating to new spacing
    print(poff.nrec, poff.npix)
    poff.nrec = int(poff.nrec / poff.azsp * azimuth_spacing)
    poff.npix = int(poff.npix / poff.rgsp * range_spacing)
    print(poff.nrec, poff.npix)
    poff.rgsp = range_spacing
    poff.azsp = azimuth_spacing
    poff.x_end = poff.x_start + (poff.npix - 1) * poff.rgsp
    poff.y_end = poff.y_start + (poff.nrec - 1) * poff.azsp

    xoff = congrid2d(xoff_masked.filled(0), [poff.nrec, poff.npix], NoData=0)
    yoff = congrid2d(yoff_masked.filled(0), [poff.nrec, poff.npix], NoData=0)

    del xoff_masked, yoff_masked

    off_masked = xoff + 1j * yoff

    del xoff, yoff

    off_masked.byteswap().tofile(id1 + '-' + id2 + '.offmap.off.new.interp')
    print(poff.snpix)

    poff.write(id1 + '-' + id2 + '.offmap.par.interp')

    os.system('rasmph ' + id1 + '-' + id2 + '.offmap.off.new.interp ' + str(
        poff.npix))

    f = open('bat_inter.' + id1 + '-' + id2, 'w')
    f.write(
        interf + ' ' + id1 + '.slc ' + id2 + '.slc ' + id1 + '.par ' + id2 + '.par ' + id1 + '-' + id2 + '.offmap.par.interp ' + id1 + '-' + id2 + '.offmap.off.new.interp ' + id1 + '.pwr1 ' + id2 + '.pwr2 coco' + id1 + '-' + id2 + '.dat ' + str(
            int(range_spacing / 2)) + ' ' + str(
            int(azimuth_spacing / 2)) + ' ' + str(
            int(range_spacing)) + ' ' + str(int(azimuth_spacing)))
    f.close()

    os.system('chmod 777 bat_inter.' + id1 + '-' + id2)
