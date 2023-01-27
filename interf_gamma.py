#!/usr/bin/env python
u"""
Enrico Ciraci' - 01/2023

Compute Interferogram for the selected pair - GAMMA calculation Approach.

usage: interf_gamma.py [-h] [--directory DIRECTORY]
    [--out_directory OUT_DIRECTORY] [--filter] [--keep]
    reference secondary {gis,gimp,greenland,ais,antarctica,bedmap2}

Compute Interferogram Differential Interferogram using GAMMA Software.

positional arguments:
  reference             Reference SLC.
  secondary             Secondary SLC.
  {gis,gimp,greenland,ais,antarctica,bedmap2}
                        Digital Elevation Model used to Remove Topographic
                        Contribution from Flattened Interferogram.

options:
  -h, --help            show this help message and exit
  --directory DIRECTORY, -D DIRECTORY
                        Data directory.
  --out_directory OUT_DIRECTORY, -O OUT_DIRECTORY
                        Output directory.
  --filter, -F          Use ADF filter to smooth interferogram phase.
  --keep, -K            Keep intermediate processing outputs.

"""
# - Python Dependencies
from __future__ import print_function
import os
import argparse
import datetime
import shutil
import numpy as np
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
import py_gamma2019 as pg9
# - ST_Release dependencies
from scipy.signal import medfilt
from astropy.convolution import convolve, Box2DKernel
from st_release.madian_filter_off import median_filter_off
from st_release.fill_nodata import fill_nodata
from utils.path_to_dem import path_to_dem
from utils.make_dir import make_dir


def create_isp_par(data_dir: str, ref: str, sec: str,
                   algorithm: int = 1, rlks: int = 1,
                   azlks: int = 1, iflg: int = 0):
    """
    Generate a new parameter file ISP offset and interferogram parameter files
    :param data_dir: absolute path to data directory
    :param ref: reference SLC
    :param sec: secondary SLC
    :param algorithm: offset estimation algorithm
    :param rlks: number of interferogram range looks
    :param azlks: number of interferogram azimuth looks
    :param iflg: interactive mode flag [0, 1]
    :return: None
    """
    # - Create and update ISP offset and interferogram parameter files
    pg.create_offset(
        os.path.join(data_dir, f'{ref}.par'),
        os.path.join(data_dir, f'{sec}.par'),
        os.path.join(data_dir, f'{ref}-{sec}.par'),
        algorithm, rlks, azlks, iflg
    )
    # - Initial SLC image offset estimation from orbit state-vectors
    # - and image parameters
    pg.init_offset_orbit(
        os.path.join(data_dir, f'{ref}.par'),
        os.path.join(data_dir, f'{sec}.par'),
        os.path.join(data_dir, f'{ref}-{sec}.par')
    )


def compute_dense_offsets(data_dir: str, out_dir: str,
                          ref: str, sec: str,
                          off_filter: int = 1,
                          search_w: int = 64, skip: int = None,
                          off_smooth: bool = False,
                          off_fill: bool = False) -> None:
    """
    Compute Dense Offsets Map between a reference SLC and a secondary SLC
    :param data_dir: absolute path to directory containing input data
    :param out_dir: absolute path to output directory
    :param ref: reference SLC [code]
    :param sec: secondary SLC [code]
    :param off_filter: outlier identification strategy [1, 2]
    :param search_w: dense offset search window [pixels]
    :param skip: dense offset search skip [pixels] - def None
    :param off_smooth: smooth offsets map [True, False] - def False
    :param off_fill: fill offsets map missing values [True, False] - def False
    :return: None
    """
    # - Offsets Processing Parameters
    filter_strategy = off_filter    # - Offsets Filtering Strategy
    smooth_off = off_smooth         # - Smooth Offsets Map
    fill_off = off_fill             # - Fill Offsets Map
    pair_name = f'{ref}-{sec}'      # - Pair name
    # - Range and azimuth offset polynomial estimation with offset_fit
    off_weight = 'ccp'  # - Offsets Fit weights cross-corr or SNR [ccp, snr]
    poly_order = 3      # - Polynomial order for offset estimation

    if off_filter not in [1, 2]:
        raise ValueError('Invalid Offsets Filter Strategy. Must be 1 or 2.')

    # - Set Skip Value equal to half of Search Window
    if skip is None:
        skip = search_w // 2

    # - Estimates the range and azimuth registration offset fields
    # - on a preliminary coarse resolution grid
    print('#  - Estimate the range and azimuth offset fields.')
    c_search_w = search_w
    c_skip = skip
    print(f'#  - Search Window: {c_search_w}, Skip: {c_skip}')
    pg.offset_pwr_tracking(
        os.path.join(data_dir, f'{ref}.slc'),
        os.path.join(data_dir, f'{sec}.slc'),
        os.path.join(data_dir, f'{ref}.par'),
        os.path.join(data_dir, f'{sec}.par'),
        os.path.join(data_dir, f'{pair_name}.par'),
        os.path.join(out_dir, f'{pair_name}.offmap'),
        os.path.join(out_dir, f'{pair_name}.offmap.ccp'),
        c_search_w, c_search_w,
        os.path.join(out_dir, f'{pair_name}.offmap.txt'),
        '-', '-', c_skip, c_skip, '-', '-', '-', '-', '-', '-',
    )

    # - Read the offset parameter file
    off_param = pg.ParFile(os.path.join(out_dir, f'{pair_name}.par'))
    rn_min = int(off_param.par_dict['offset_estimation_starting_range'][0])
    rn_max = int(off_param.par_dict['offset_estimation_ending_range'][0])
    az_min = int(off_param.par_dict['offset_estimation_starting_azimuth'][0])
    az_max = int(off_param.par_dict['offset_estimation_ending_azimuth'][0])
    rn_smp = int(off_param.par_dict['offset_estimation_range_samples'][0])
    az_smp = int(off_param.par_dict['offset_estimation_azimuth_samples'][0])
    rn_spacing = int(off_param.par_dict['offset_estimation_range_spacing'][0])
    az_spacing = int(off_param.par_dict['offset_estimation_azimuth_spacing'][0])

    # - Verify that offsets parameter file has been modified
    # - by offset_pwr_tracking
    if rn_max == 0:
        # - Read Secondary Parameter file
        sec_param = pg.ParFile(os.path.join(data_dir, f'{ref}.par'))
        rn_smp_sec = int(sec_param.par_dict['range_samples'][0])
        az_smp_sec = int(sec_param.par_dict['azimuth_lines'][0])
        rn_smp = int(rn_smp_sec / c_skip)
        az_smp = int(az_smp_sec / c_skip)

        if rn_smp * c_skip > rn_smp_sec:
            rn_smp -= 1
        if az_smp * c_skip > az_smp_sec:
            az_smp -= 1
        rn_max = rn_smp * c_skip - 1
        az_max = az_smp * c_skip - 1
        print(f'# - Range Sample: {rn_smp}')
        print(f'# - Azimuth Sample: {az_smp}')
        print(f'# - Ending Range: {rn_max}')
        print(f'# - Ending Azimuth: {az_max}')

        # - Update Offsets Parameter file
        off_param.set_value('offset_estimation_ending_range', rn_max)
        off_param.set_value('offset_estimation_ending_azimuth', az_max)
        off_param.set_value('offset_estimation_range_samples', rn_smp)
        off_param.set_value('offset_estimation_azimuth_samples', az_smp)
        off_param.set_value('offset_estimation_range_spacing', c_skip)
        off_param.set_value('offset_estimation_azimuth_spacing', c_skip)
        off_param.set_value('offset_estimation_window_width', c_search_w)
        off_param.set_value('offset_estimation_window_height', c_search_w)
        off_param.write_par(os.path.join(out_dir, f'{pair_name}.par'))

    # - Unpack Offsets Map
    o_rn, o_az, _, _, _, snr, \
        = np.loadtxt(os.path.join(out_dir, f'{pair_name}.offmap.txt'),
                     unpack=True)
    o_rn = np.array(o_rn / rn_spacing, dtype=int)
    o_az = np.array(o_az / az_spacing, dtype=int)

    # - Initialize SNR Array
    snr_array = np.zeros((az_smp, rn_smp))
    snr_array[o_az, o_rn] = snr
    snr_array.byteswap() \
        .tofile(os.path.join(out_dir, f'{pair_name}.offmap.snr'))

    # - Run Gamma offset_fit: Range and azimuth offset polynomial estimation
    # - Note: Cross-correlation coefficients of SNR values can be set as
    # -       Linear Fit weights.
    pg.offset_fit(
        os.path.join(out_dir, f'{pair_name}.offmap'),
        os.path.join(out_dir, f'{pair_name}.offmap.{off_weight}'),
        os.path.join(out_dir, f'{pair_name}.par'),
        '-', '-', '-', poly_order, 0
    )

    # - Run Gamma offset_sub: Subtraction of polynomial
    # - from range and azimuth offset estimates
    pg.offset_sub(
        os.path.join(out_dir, f'{pair_name}.offmap'),
        os.path.join(out_dir, f'{pair_name}.par'),
        os.path.join(out_dir, f'{pair_name}.offmap.res'),
    )

    # - Run GAMMA rasmph: Generate 8-bit raster graphics image of the phase
    # - and intensity of complex data - Show Interpolated Offsets Map
    pg9.rasmph(os.path.join(out_dir, f'{pair_name}.offmap.res'),
               rn_smp, '-', '-', '-', '-', '-', '-', '-',
               os.path.join(out_dir, f'{pair_name}.offmap.res.bmp'))

    # - Process Offsets Map
    # - > Remove Outliers
    # - > Apply Smoothing Filter
    # - > Fill in Nodata [Optional]
    off_map \
        = pg.read_image(os.path.join(out_dir, f'{pair_name}.offmap.res'),
                        width=rn_smp, dtype='fcomplex')

    # - Remove Erroneous Offsets s by apply Median Filter.
    if filter_strategy == 1:
        # - Filtering strategy 1 - see c_off4intf.py
        med_filt_size = 9  # - Median filter Kernel Size
        med_thresh = 1  # - Median filter Threshold
    elif filter_strategy == 2:
        # - Filtering Strategy 2 - see c_off3intf.pro
        med_filt_size = 15  # - Median filter Kernel Size
        med_thresh = 0.5  # - Median filter Threshold
    else:
        raise ValueError('# - Unknown filtering strategy selected.')
    # - Compute outlier Mask
    mask = median_filter_off(off_map, size=med_filt_size, thre=med_thresh)

    # - Set Outliers Mask borders equal to 1
    mask[:, 0:2] = 1
    mask[:, rn_smp - 2:] = 1
    mask[0:2, :] = 1
    mask[az_smp - 2:, :] = 1

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

    # - Smooth Offsets using 7x7 Boxcar Filter
    smth_kernel_size = 7
    kernel = Box2DKernel(smth_kernel_size)
    if smooth_off:
        xoff_masked \
            = convolve(xoff_masked, kernel, boundary='extend')
        yoff_masked \
            = convolve(yoff_masked, kernel, boundary='extend')

    # - Set to NaN offsets pixels that have a zero value in
    # - either of the two directions.
    ind_zero = np.where((xoff_masked == 0) | (yoff_masked == 0))
    xoff_masked[ind_zero] = np.nan
    yoff_masked[ind_zero] = np.nan

    # - Fill Offsets Map Nodata
    if fill_off:
        print('# - Filling Gaps Offsets Map by interpolation.')
        x_mask = np.ones(np.shape(xoff_masked))
        x_mask[np.where(np.isnan(xoff_masked))] = 0
        xoff_masked = fill_nodata(xoff_masked, x_mask,
                                  max_search_dist=1000, smth_iter=10)
        y_mask = np.ones(np.shape(yoff_masked))
        y_mask[np.where(np.isnan(yoff_masked))] = 0
        yoff_masked = fill_nodata(yoff_masked, y_mask,
                                  max_search_dist=1000, smth_iter=10)

    # - Set to NaN offsets pixels to Zero
    xoff_masked[np.isnan(xoff_masked)] = 0
    yoff_masked[np.isnan(yoff_masked)] = 0

    # - Save Offsets as a complex array
    off_masked = xoff_masked + 1j * yoff_masked

    off_masked.byteswap() \
        .tofile(os.path.join(out_dir, f'{pair_name}.offmap.res.filt'))

    # - Show Smoothed Offsets Map
    pg9.rasmph(os.path.join(out_dir, f'{pair_name}.offmap.res.filt'), rn_smp)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="""Compute Interferogram Differential Interferogram using 
        GAMMA Software."""
    )
    parser.add_argument('reference', type=str, help='Reference SLC.')

    parser.add_argument('secondary', type=str, help='Secondary SLC.')

    parser.add_argument('dem', type=str,
                        choices=['gis', 'gimp', 'greenland',
                                 'ais', 'antarctica', 'bedmap2'],
                        help='Digital Elevation Model used to '
                             'Remove Topographic Contribution '
                             'from Flattened Interferogram.',
                        )

    parser.add_argument('--directory', '-D', help='Data directory.',
                        default=os.getcwd())

    parser.add_argument('--out_directory', '-O', help='Output directory.',
                        default=os.getcwd())

    parser.add_argument('--filter', '-F',
                        help='Use ADF filter to smooth interferogram phase.',
                        action='store_true')

    parser.add_argument('--keep', '-K',
                        help='Keep intermediate processing outputs.',
                        action='store_true')

    parser.add_argument('--pdoff', '-p',
                        help='Compute preliminary dense offsets field.',
                        action='store_true')

    args = parser.parse_args()

    # - Path to Test directory
    data_dir = args.directory       # - Path to data directory
    out_dir = args.out_directory    # - Path to output directory

    # - Processing Parameters
    ref = args.reference        # - Reference SLC
    sec = args.secondary        # - Secondary SLC

    # - Create New ISP Parameter file
    create_isp_par(data_dir, ref, sec)

    # - Estimate Range and Azimuth Preliminary
    # - Registration offset fields Preliminary Offset
    if args.pdoff:
        pg.offset_pwr_tracking(
            os.path.join(data_dir, f'{ref}.slc'),
            os.path.join(data_dir, f'{sec}.slc'),
            os.path.join(data_dir, f'{ref}.par'),
            os.path.join(data_dir, f'{sec}.par'),
            os.path.join(data_dir, f'{ref}-{sec}.par'),
            os.path.join(out_dir, f'sparse_offsets'),
            os.path.join(out_dir, f'sparse_offsets.ccp'),
            64, 64,
            os.path.join(out_dir, f'sparse_offsets.txt'),
            '-', '-', 32, 32, '-', '-', '-', '-', '-', '-',
        )
    else:
        pg.offset_pwr(os.path.join(data_dir, f'{ref}.slc'),
                      os.path.join(data_dir, f'{sec}.slc'),
                      os.path.join(data_dir, f'{ref}.par'),
                      os.path.join(data_dir, f'{sec}.par'),
                      os.path.join(data_dir, f'{ref}-{sec}.par'),
                      os.path.join(data_dir, f'sparse_offsets'),
                      os.path.join(data_dir, f'sparse_offsets.ccp'),
                      64, 64,  os.path.join(data_dir, f'sparse_offsets.txt'),
                      '-', 64, 128
                      )

    # - Estimate range and azimuth offset polynomial
    # - Update ISP parameter file - offsets polynomial
    pg.offset_fit(os.path.join(data_dir, f'sparse_offsets'),
                  os.path.join(data_dir, f'sparse_offsets.ccp'),
                  os.path.join(data_dir, f'{ref}-{sec}.par'),
                  '-', '-', '-', 3)

    # - SLC_interp - registers SLC-2 to the reference geometry,
    # -              that is the geometry of SLC-1.
    pg.SLC_interp(os.path.join(data_dir, f'{sec}.slc'),
                  os.path.join(data_dir, f'{ref}.par'),
                  os.path.join(data_dir, f'{sec}.par'),
                  os.path.join(data_dir, f'{ref}-{sec}.par'),
                  os.path.join(data_dir, f'{sec}.reg.slc'),
                  os.path.join(data_dir, f'{sec}.reg.par'),
                  '-', '-', 0, 7
                  )
    # - Create New ISP Parameter file
    create_isp_par(data_dir, ref, f'{sec}.reg')

    # - Compute Dense Offsets Map between the reference SLC and the
    # - registered secondary SLC.
    compute_dense_offsets(data_dir, out_dir, ref, f'{sec}.reg', off_filter=1,
                          search_w=64, off_smooth=True, off_fill=False)

    # - Generate a copy of the dense offsets parameter file
    shutil.copy(os.path.join(data_dir, f'{ref}-{sec}.reg.par'),
                os.path.join(data_dir, f'dense_offsets.par'))

    # - Resample the registered secondary SLC to the reference SLC
    # - using the using a 2-D offset map computed above.
    pg.SLC_interp_map(os.path.join(data_dir, f'{sec}.reg.slc'),
                      os.path.join(data_dir, f'{ref}.par'),
                      os.path.join(data_dir, f'{sec}.reg.par'),
                      os.path.join(data_dir, f'{ref}-{sec}.reg.par'),
                      os.path.join(data_dir, f'{sec}.reg2.slc'),
                      os.path.join(data_dir, f'{sec}.reg2.par'),
                      os.path.join(data_dir, f'dense_offsets.par'),
                      os.path.join(data_dir, f'{ref}-{sec}.reg.offmap.'
                                             f'res.filt'),
                      '-', '-', 0, 7
                      )

    # - Generate a new parameter file ISP offset and interferogram
    # - parameter files.
    # - Create New ISP Parameter file
    create_isp_par(data_dir, ref, f'{sec}.reg2')

    # - Compute Interferogram
    pg.SLC_intf(os.path.join(data_dir, f'{ref}.slc'),
                os.path.join(data_dir, f'{sec}.reg2.slc'),
                os.path.join(data_dir, f'{ref}.par'),
                os.path.join(data_dir, f'{sec}.reg2.par'),
                os.path.join(data_dir, f'{ref}-{sec}.reg2.par'),
                os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf'),
                32, 32      # number of range/azimuth looks
                )
    # - Estimate baseline from orbit state vectors
    pg.base_orbit(os.path.join(data_dir, f'{ref}.par'),
                  os.path.join(data_dir, f'{sec}.reg2.par'),
                  os.path.join(data_dir, f'base{ref}-{sec}.reg2.dat'),
                  )

    # - Estimate and Remove Flat Earth Contribution from the Interferogram
    pg.ph_slope_base(os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf'),
                     os.path.join(data_dir, f'{ref}.par'),
                     os.path.join(data_dir, f'{ref}-{sec}.reg2.par'),
                     os.path.join(data_dir, f'base{ref}-{sec}.reg2.dat'),
                     os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat'),
                     )
    # - Calculate a multi-look intensity (MLI) image from the reference SLC
    pg.multi_look(os.path.join(data_dir, f'{ref}.slc'),
                  os.path.join(data_dir, f'{ref}.par'),
                  os.path.join(data_dir, f'{ref}.mli'),
                  os.path.join(data_dir, f'{ref}.mli.par'),
                  32, 32
                  )

    # - Extract interferogram dimensions from its parameter file
    igram_param_dict \
        = pg.ParFile(os.path.join(data_dir, f'{ref}-{sec}.reg2.par'),).par_dict
    # - read interferogram number of columns
    interf_width = int(igram_param_dict['interferogram_width'][0])
    interf_lines = int(igram_param_dict['interferogram_azimuth_lines'][0])
    print(f'# - Interferogram Size: {interf_lines} x {interf_width}')

    # - Adaptive interferogram filter using the power spectral density
    pg.adf(os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat'),
           os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat.filt'),
           os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat.coh'),
           interf_width
           )

    # - Generate 8-bit greyscale raster image of intensity multi-looked SLC
    pg9.raspwr(os.path.join(data_dir, f'{ref}.mli'), interf_width)

    # - Show Output Interferogram
    pg9.rasmph_pwr(
        os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat.filt'),
        os.path.join(data_dir, f'{ref}.mli.bmp'), interf_width
    )

    # - Estimate and Remove Topographic Phase from the flattened interferogram
    dem = args.dem
    dem_info = path_to_dem(dem)
    dem_info['path'] = dem_info['path']
    dem_par = os.path.join(dem_info['path'].replace(' ', '\ '), dem_info['par'])
    dem = os.path.join(dem_info['path'].replace(' ', '\ '), dem_info['dem'])
    data_dir_gc = data_dir.replace(' ', '\ ')

    pg.gc_map(os.path.join(data_dir_gc, f'{ref}.par'),
              os.path.join(data_dir_gc, f'{ref}-{sec}.reg2.par'),
              dem_par,  # - DEM/MAP parameter file
              dem,  # - DEM data file (or constant height value)
              dem_info['par'],  # - DEM segment used...
              'DEMice_gc',  # - DEM segment used for output products...
              'gc_icemap',  # - geocoding lookup table (fcomplex)
              dem_info['oversample'], dem_info['oversample'],
              'sar_map_in_dem_geometry',
              '-', '-', 'inc.geo', '-', '-', '-', '-', '2', '-'
              )

    # - Extract DEM Size from parameter file
    dem_par_path = os.path.join('.', 'DEM_gc_par')
    dem_param_dict = pg.ParFile(dem_par_path).par_dict
    dem_width = int(dem_param_dict['width'][0])
    dem_nlines = int(dem_param_dict['nlines'][0])

    print(f'# - DEM Size: {dem_nlines} x {dem_width}')

    # - Forward geocoding transformation using a lookup table
    pg.geocode('gc_icemap', 'DEMice_gc', dem_width, 'hgt_icemap',
               interf_width, interf_lines)
    pg.geocode('gc_icemap', 'inc.geo', dem_width, 'inc',
               interf_width, interf_lines)

    # - Invert geocoding lookup table
    pg.gc_map_inversion('gc_icemap', dem_width, 'gc_map_invert',
                        interf_width, interf_lines)

    # - Geocoding of Reference SLC power using a geocoding lookup table
    pg.geocode_back(os.path.join(data_dir, f'{ref}.mli'), interf_width,
                    'gc_icemap',
                    os.path.join(data_dir, f'{ref}.mli.geo'),
                    dem_width, dem_nlines)
    pg9.raspwr(os.path.join(data_dir, f'{ref}.mli.geo'), dem_width)

    # - Remove Interferometric Phase component due to surface Topography.
    # - Simulate unwrapped interferometric phase using DEM height.
    pg.phase_sim(os.path.join(data_dir, f'{ref}.par'),
                 os.path.join(data_dir, f'{ref}-{sec}.reg2.par'),
                 os.path.join(data_dir, f'base{ref}-{sec}.reg2.dat'),
                 'hgt_icemap',
                 'sim_phase', 1, 0, '-'
                 )
    # - Create DIFF/GEO parameter file for geocoding and
    # - differential interferometry
    pg.create_diff_par(os.path.join(data_dir, f'{ref}-{sec}.reg2.par'),
                       os.path.join(data_dir, f'{ref}-{sec}.reg2.par'),
                       'DIFF_par', '-', 0)

    # - Subtract topographic phase from interferogram
    pg.sub_phase(os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat'),
                 'sim_phase', 'DIFF_par',
                 os.path.join(data_dir,
                              f'coco{ref}-{sec}.reg2.intf.flat.topo_off'), 1
                 )
    # - Show interferogram w/o topographic phase
    pg9.rasmph_pwr(os.path.join(data_dir,
                                f'coco{ref}-{sec}.reg2.intf.flat.topo_off'),
                   os.path.join(data_dir, f'{ref}.mli'), interf_width)

    # - Geocode Output interferogram
    # - Reference Interferogram look-up table
    ref_gcmap = os.path.join('.', 'gc_icemap')

    # - geocode interferogram
    pg.geocode_back(
        os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat.topo_off'),
        interf_width,  ref_gcmap,
        os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat.topo_off.geo'),
        dem_width, dem_nlines, '-', 1
    )

    # - Show Geocoded interferogram
    pg9.rasmph_pwr(
        os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat.topo_off.geo'),
        os.path.join(data_dir, f'{ref}.mli.geo'),  dem_width
    )

    if args.filter:
        # - Smooth the obtained interferogram with pg.adf
        # - Adaptive interferogram filter using the power spectral density.
        pg.adf(os.path.join(data_dir, f'coco{ref}-{sec}.flat.topo_off'),
               os.path.join(data_dir, f'coco{ref}-{sec}.flat.topo_off.filt'),
               os.path.join(data_dir,
                            f'coco{ref}-{sec}.flat.topo_off.filt.coh'),
               dem_width)
        # - Show filtered interferogram
        pg9.rasmph_pwr(
            os.path.join(data_dir, f'coco{ref}-{sec}.flat.topo_off.filt'),
            os.path.join(data_dir, f'{ref}.pwr1.geo'), dem_width
        )

        # - Smooth Geocoded Interferogram
        pg.adf(os.path.join(data_dir, f'coco{ref}-{sec}.flat.topo_off.geo'),
               os.path.join(data_dir,
                            f'coco{ref}-{sec}.flat.topo_off.geo.filt'),
               os.path.join(data_dir,
                            f'coco{ref}-{sec}.flat.topo_off.geo.filt.coh'),
               dem_width)
        # - Show filtered interferogram
        pg9.rasmph_pwr(
            os.path.join(data_dir, f'coco{ref}-{sec}.flat.topo_off.geo.filt'),
            os.path.join(data_dir, f'{ref}.pwr1.geo'), dem_width
        )

    # - Change Permission Access to all the files contained inside the
    # - output directory.
    for out_file in os.listdir('.'):
        os.chmod(out_file, 0o0755)

    if not args.keep:
        # - Rename interferometric outputs
        coco_list = [os.path.join(data_dir, x) for x in os.listdir(data_dir)
                     if x.startswith('coco') or x.startswith('base')]
        for co in coco_list:
            if os.path.isfile(co):
                os.rename(co, co.replace('_r.reg2.', '.'))

        # - Save Offsets Maps inside a subdirectory
        off_dir = make_dir('.', 'offsets')
        off_list = [os.path.join(data_dir, x) for x in os.listdir(data_dir)
                    if 'offsets' in x or 'offmap' in x]
        for off in off_list:
            if os.path.isfile(off):
                off_name = off.split('/')[-1]
                try:
                    shutil.move(off, os.path.join(off_dir, off_name))
                except shutil.SameFileError:
                    os.remove(off)

        # - Remove intermediate processing outputs
        out_d_list = [os.path.join(data_dir, x) for x in os.listdir(data_dir)
                      if not x.startswith('.')]
        for out in out_d_list:
            if '_r.reg' in out and os.path.isfile(out):
                os.remove(out)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
