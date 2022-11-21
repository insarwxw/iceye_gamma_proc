#!/usr/bin/env python

import os
import numpy as np
from scipy.signal import medfilt
from st_release.fparam import off_param, isp_param
from st_release.madian_filter_off import median_filter_off
from st_release.congrid2d import congrid2d

import py_gamma as pg


def c_off4intf(data_dir: str, id1: str, id2: str,
               interf_bin: str = '$ST_PATH/COMMON/GAMMA_OLD/bin/interf_offset64b'
               ) -> None:

    # - Read Offsets Map Parameters and extract
    # - azimuth and range pixel spacing.
    poff = off_param()
    poff.load(os.path.join(data_dir, id1 + '-' + id2 + '.offmap.par'))
    range_spacing = poff.rgsp
    azimuth_spacing = poff.azsp
    print('# - Range spacing :', range_spacing)
    print('# - Azimuth spacing :', azimuth_spacing)

    # - Read Offsets Map
    offset_map_path = os.path.join(data_dir, id1 + '-' + id2 + '.offmap.off')
    off_map = np.fromfile(offset_map_path, dtype=np.complex64)\
        .reshape(poff.nrec, poff.npix).byteswap()

    # - Generate Ramp - Linear Ramp in the azimuth/range domain
    x = np.ones([poff.nrec, 1], dtype='float32') \
        * (np.arange(poff.npix, dtype='float32').reshape([1, poff.npix]))
    y = np.ones([1, poff.npix], dtype='float32') \
        * np.arange(poff.nrec, dtype='float32').reshape([poff.nrec, 1])

    # - Generate Range and Azimuth axes
    # - Note multiplication for pixel spacing.
    x_var = poff.x_start + x * poff.rgsp
    y_var = poff.y_start + y * poff.azsp

    # - Generate Polynomial Ramp
    ramp_offx = poff.xoff[0] + x_var * poff.xoff[1] + y_var * poff.xoff[2]
    ramp_offy = poff.yoff[0] + x_var * poff.yoff[1] + y_var * poff.yoff[2]

    # - Remove Erroneous Offsets s by apply Median Filter.
    medfilt_size = 9        # - Median filter Kernel Size
    medthre = 1             # - Median filter Threshold
    mask = median_filter_off(off_map, size=medfilt_size, thre=medthre)

    # - Set Outliers Mask borders equal to 1
    mask[:, 0:2] = 1
    mask[:, poff.npix - 2:] = 1
    mask[0:2, :] = 1
    mask[poff.nrec - 2:, :] = 1
    # - Apply Outliers Mask to Offsets Map
    xoff_masked = np.ma.array(off_map.real, mask=mask)
    yoff_masked = np.ma.array(off_map.imag, mask=mask)

    # - Multiply Masked Offsets Maps for a second mask generated by applying
    # - a median filter, with kernel size of 3x3 to the masked offsets.
    xoff_masked.mask = xoff_masked.mask | \
                       (medfilt(xoff_masked.filled(fill_value=0), 3) == 0) | \
                       (medfilt(yoff_masked.filled(fill_value=0), 3) == 0)

    yoff_masked.mask = yoff_masked.mask | \
                       (medfilt(xoff_masked.filled(fill_value=0), 3) == 0) | \
                       (medfilt(yoff_masked.filled(fill_value=0), 3) == 0)

    # - Subtract Polynomial Ramp from Offsets Map
    xoff_masked -= ramp_offx
    yoff_masked -= ramp_offy

    # - Interpolate Masked Offsets to the Interferogram Grid.
    print('# - Interpolating Offsets to Interferogram Grid')
    print(f'# - Input Offsets Grid Shape: [{poff.nrec},{poff.npix}]')
    poff.nrec = int(poff.nrec / poff.azsp * azimuth_spacing)
    poff.npix = int(poff.npix / poff.rgsp * range_spacing)

    print(f'# - Interferogram Grid Shape: [{poff.nrec},{poff.npix}]')
    poff.rgsp = range_spacing
    poff.azsp = azimuth_spacing
    poff.x_end = poff.x_start + (poff.npix - 1) * poff.rgsp
    poff.y_end = poff.y_start + (poff.nrec - 1) * poff.azsp

    # - Interpolate Offsets to Interferogram Grid
    x_off = congrid2d(xoff_masked.filled(0), [poff.nrec, poff.npix], NoData=0)
    y_off = congrid2d(yoff_masked.filled(0), [poff.nrec, poff.npix], NoData=0)

    # - Save Offsets as a complex array
    off_masked = x_off + 1j * y_off
    off_masked.byteswap()\
        .tofile(os.path.join(data_dir, id1 + '-' + id2
                             + '.offmap.off.new.interp'))
    # - Save Interpolated Offsets Parameters
    poff.write(os.path.join(data_dir, id1 + '-' + id2 + '.offmap.par.interp'))

    # - Run GAMMA rasmph: Generate 8-bit raster graphics image of the phase
    # - and intensity of complex data - Show Interpolated Offsets Map
    pg.rasmph(os.path.join(data_dir, id1 + '-' + id2
                           + '.offmap.off.new.interp'), poff.npix)

    # - Write Bash Script to run to compute the interferogram
    bat_inter_path = os.path.join(data_dir, 'bat_inter.' + id1 + '-' + id2)
    with open(bat_inter_path, 'w') as i_fid:
        ref_slc = id1 + '.slc'
        sec_slc = id2 + '.slc'
        ref_par = id1 + '.par'
        sec_par = id2 + '.par'
        offset_par = id1 + '-' + id2 + '.offmap.par.interp'
        offset_interp = id1 + '-' + id2 + '.offmap.off.new.interp'
        ref_pwr1 = id1 + '.pwr1'
        sec_par1 = id2 + '.pwr2'
        intef_path = 'coco' + id1 + '-' + id2 + '.dat'
        nrlk = int(range_spacing / 2)
        nazlk = int(azimuth_spacing / 2)
        rstep = int(range_spacing)
        zstep = int(azimuth_spacing)
        i_fid.write(f'{interf_bin} {ref_slc} {sec_slc} {ref_par} {sec_par} '
                    f'{offset_par} {offset_interp} {ref_pwr1} {sec_par1} '
                    f'{intef_path} {nrlk} {nazlk} {rstep} {zstep}')

    # - Change access permissions to the bash script
    os.chmod(bat_inter_path, 0o777)
