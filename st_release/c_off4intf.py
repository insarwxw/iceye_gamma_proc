#!/usr/bin/env python
u"""
c_off4intf.py
Written by  Enrico Ciraci' - 11/2022
Originally written by  Jeremie Mouginot - 2018

Process dense offsets generated by AMPCOR.

This script is a new Python implementation of:
- ST_RELEASE/COMMON/IDL/c_off4intf.pro
- ST_RELEASE/COMMON/PYTHON/c_off4intf.py

"""
# - Python Dependencies
import os
import numpy as np
from scipy.signal import medfilt
from astropy.convolution import convolve, Box2DKernel
# - ST_Release dependencies
from st_release.fparam import off_param
from st_release.madian_filter_off import median_filter_off
from st_release.congrid2d import congrid2d
from st_release.fill_nodata import fill_nodata
# - GAMMA Python Binding
import py_gamma2019 as pg9


def c_off4intf(data_dir: str, id1: str, id2: str,
               range_spacing: int = None,
               azimuth_spacing: int = None,
               filter_strategy: int  = 1,
               smooth: bool =False,
               fill: bool = False,
               nrlks: int = None,
               nazlks: int = None,
               interf_bin: str = '$ST_PATH/COMMON/GAMMA_OLD'
                                 '/bin/interf_offset64b'
               ) -> None:
    """
    Process dense offsets generated by AMPCOR
    :param data_dir: absolute path to the data directory
    :param id1: reference SLC
    :param id2: secondary SLC
    :param range_spacing: range spacing [def. None]
    :param azimuth_spacing: azimuth spacing [def. None]
    :param filter_strategy: outliers filtering strategy [def. 1]
    :param smooth: smooth offsets [def. False]
    :param fill: fill gaps in offsets [def. False]
    :param nrlks: number of looks in range [def. None]
    :param nazlk: number of looks in azimuth [def. None]
    :param interf_bin: GAMMA interf_offset binary
    :return: None
    """
    # - Read Offsets Map Parameters and extract
    # - azimuth and range pixel spacing.
    poff = off_param()
    poff.load(os.path.join(data_dir, id1 + '-' + id2 + '.offmap.par'))

    if range_spacing is None:
        range_spacing = int(150. / poff.rgsp)

    if azimuth_spacing is None:
        azimuth_spacing = int(150. / poff.azsp)

    print('# - Running c_off4int.py')
    print(f'# - Range spacing : {range_spacing}')
    print(f'# - Azimuth spacing : {azimuth_spacing}')

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
    if filter_strategy == 1:
        # - Filtering strategy 1 - see c_off4intf.py
        med_filt_size = 9            # - Median filter Kernel Size
        med_thresh = 1               # - Median filter Threshold
    elif filter_strategy == 2:
        # - Filtering Strategy 2 - see c_off3intf.pro
        med_filt_size = 15           # - Median filter Kernel Size
        med_thresh = 0.5             # - Median filter Threshold
    else:
        raise ValueError('# - Unknown filtering strategy selected.')

    mask = median_filter_off(off_map, size=med_filt_size, thre=med_thresh)

    # - Set Outliers Mask borders equal to 1
    mask[:, 0:2] = 1
    mask[:, poff.npix - 2:] = 1
    mask[0:2, :] = 1
    mask[poff.nrec - 2:, :] = 1

    # - Apply Outliers Mask to Offsets Map
    xoff_masked = off_map.real.copy()
    yoff_masked = off_map.imag.copy()
    xoff_masked[mask] = 0
    yoff_masked[mask] = 0

    # - Run as 5x5 median filter to locate isolated offsets values - offsets
    # - surrounded by zeros and set them to zero.
    # - Find more details in step2 of off_filter.pro
    g_mask = (mask | (medfilt(xoff_masked, 5) == 0)
              | (medfilt(yoff_masked, 5) == 0))
    xoff_masked[g_mask] = np.nan
    yoff_masked[g_mask] = np.nan

    # - Smooth Offsets Map using a 3x3 Median Filter
    xoff_masked = medfilt(xoff_masked, 3)
    yoff_masked = medfilt(yoff_masked, 3)

    # - Smooth Offsets suing 7x7 Boxcar Filter
    smth_kernel_size = 7
    kernel = Box2DKernel(smth_kernel_size)
    if smooth:
        xoff_masked \
            = convolve(xoff_masked, kernel, boundary='extend')
        yoff_masked \
            = convolve(yoff_masked, kernel, boundary='extend')

    # - Set to NaN offsets pixels that have a zero value in
    # - either of the two directions.
    ind_zero = np.where((xoff_masked == 0) | (yoff_masked == 0))
    xoff_masked[ind_zero] = np.nan
    yoff_masked[ind_zero] = np.nan

    # - Fill Missing Values
    if fill:
        print('# - Filling Gaps Offsets Map by interpolation.')
        x_mask = np.ones(np.shape(xoff_masked))
        x_mask[np.where(np.isnan(xoff_masked))] = 0
        xoff_masked = fill_nodata(xoff_masked, x_mask,
                                  max_search_dist=1000, smth_iter=10)
        y_mask = np.ones(np.shape(yoff_masked))
        y_mask[np.where(np.isnan(yoff_masked))] = 0
        yoff_masked = fill_nodata(yoff_masked, y_mask,
                                  max_search_dist=1000, smth_iter=10)

    # - Subtract Polynomial Ramp from Offsets Map
    xoff_masked -= ramp_offx
    yoff_masked -= ramp_offy

    # - Regrid Masked Offsets to the Selected Resolution.
    print('# - Interpolating Offsets to Interferogram Grid.')
    print(f'# - Input Offsets Grid Shape: [{poff.nrec},{poff.npix}]')
    poff.nrec = int(poff.nrec / poff.azsp * azimuth_spacing)
    poff.npix = int(poff.npix / poff.rgsp * range_spacing)

    print(f'# - Interferogram Grid Shape: [{poff.nrec},{poff.npix}]')
    poff.rgsp = range_spacing
    poff.azsp = azimuth_spacing
    poff.x_end = poff.x_start + (poff.npix - 1) * poff.rgsp
    poff.y_end = poff.y_start + (poff.nrec - 1) * poff.azsp

    # - Interpolate Offsets to Interferogram Grid
    xoff_masked[np.isnan(xoff_masked)] = 0
    yoff_masked[np.isnan(yoff_masked)] = 0
    x_off = congrid2d(xoff_masked, [poff.nrec, poff.npix], NoData=0)
    y_off = congrid2d(yoff_masked, [poff.nrec, poff.npix], NoData=0)

    # - Save Offsets as a complex array
    off_masked = x_off + 1j * y_off
    off_masked.byteswap()\
        .tofile(os.path.join(data_dir, id1 + '-' + id2
                             + '.offmap.off.new.interp'))
    # - Save Interpolated Offsets Parameters
    poff.write(os.path.join(data_dir, id1 + '-' + id2 + '.offmap.par.interp'))

    # - Run GAMMA rasmph: Generate 8-bit raster graphics image of the phase
    # - and intensity of complex data - Show Interpolated Offsets Map
    pg9.rasmph(os.path.join(data_dir, id1 + '-' + id2
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
        if nrlks is None:
            nrlks = int(range_spacing / 2)
        if nazlks is None:
            nazlks = int(azimuth_spacing / 2)
        rstep = int(range_spacing)
        zstep = int(azimuth_spacing)
        i_fid.write(f'{interf_bin} {ref_slc} {sec_slc} {ref_par} {sec_par} '
                    f'{offset_par} {offset_interp} {ref_pwr1} {sec_par1} '
                    f'{intef_path} {nrlks} {nazlks} {rstep} {zstep}')

    # - Change access permissions to the bash script
    os.chmod(bat_inter_path, 0o777)
