#!/usr/bin/env python
u"""
dense_offsets_map.py

Written by Enrico Ciraci' (12/2022)

Estimates the range and azimuth registration offset fields using cross
correlation optimization of the detected SLC data.
For more details, see: GAMMA - dense_offsets_map

usage: dense_offsets_map.py [-h] [--directory DIRECTORY]
    [--out_directory OUT_DIRECTORY] [--search_w SEARCH_W] [--skip SKIP]
    [--interp_off] [--out_off_spacing OUT_OFF_SPACING] [--off_weight {ccp,snr}]
    [--off_filter {1,2}] [--off_smooth] [--off_fill] [--normalize] [--intf]
    reference secondary

Compute Dense Offset Map - AMPCOR.

positional arguments:
  reference             Reference SLC.
  secondary             Secondary SLC.

options:
  -h, --help            show this help message and exit
  --directory DIRECTORY, -D DIRECTORY
                        Data directory.
  --out_directory OUT_DIRECTORY, -O OUT_DIRECTORY
                        Output directory.
  --search_w SEARCH_W, -W SEARCH_W
                        Search Window.
  --skip SKIP, -S SKIP  Skip - Def: Search Window/2.
  --interp_off          Interpolate Offset Map to a different resolution.
  --out_off_spacing OUT_OFF_SPACING
                        Offset Map Range/Azimuth Spacing.
  --off_weight {ccp,snr}
                        Offsets polynomial weight.
  --off_filter {1,2}    Offsets filtering strategy.
  --off_smooth          Smooth offsets map.
  --off_fill            Fill offsets map.
  --normalize           Normalize Secondary Azimuth Res.
  --intf                Setup Interferogram Calcualation.



PYTHON DEPENDENCIES:
    argparse: Parser for command-line options, arguments and sub-commands
           https://docs.python.org/3/library/argparse.html
    datetime: Basic date and time types
           https://docs.python.org/3/library/datetime.html#module-datetime
    numpy: Fundamental package for scientific computing with Python
           https://numpy.org
    astropy: Community-developed python astronomy tools
           https://www.astropy.org/
    py_gamma: GAMMA's Python integration with the py_gamma module

UPDATE HISTORY:


"""
# - Python Dependencies
from __future__ import print_function
import os
import argparse
import datetime
import numpy as np
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
import py_gamma2019 as pg9
# - ST_Release dependencies
from scipy.signal import medfilt
from astropy.convolution import convolve, Box2DKernel
from st_release.madian_filter_off import median_filter_off
from st_release.congrid2d import congrid2d
from st_release.fill_nodata import fill_nodata
from st_release.resample_slc import resample_slc_azimuth, resample_slc_prf

#TODO: Add support for the following options:
# - --interp_off         Interpolate Offset Map to a different resolution.
# - --out_off_spacing    Offset Map Range/Azimuth Spacing.

def setup_intf(data_dir: str, ref: str, sec: str,
               offsets: str, offsets_par: str,
               range_spacing: int, azimuth_spacing: int) -> None:
    """
    Setup interferogram Calculation Process
    :param data_dir: data directory
    :param ref: reference SLC
    :param sec: secondary SLC
    :param offsets: Offsets Map
    :param offsets_par: Offsets Parameter File
    :param range_spacing: offsets range spacing
    :param azimuth_spacing: offsets azimuth spacing
    :return: None
    """
    # - Path to Interferogram Calculation Binary
    interf_bin = '$ST_PATH/COMMON/GAMMA_OLD/bin/interf_offset64b'
    # - Write Bash Script to run to compute the interferogram
    bat_inter_path = os.path.join(data_dir, 'bat_inter.' + ref + '-' + sec)
    with open(bat_inter_path, 'w') as i_fid:
        ref_slc = ref + '.slc'
        sec_slc = sec + '.slc'
        ref_par = ref + '.par'
        sec_par = sec + '.par'
        ref_pwr1 = ref + '.pwr1'
        sec_par1 = sec + '.pwr2'
        intef_path = 'coco' + ref + '-' + sec + '.dat'
        nrlk = int(range_spacing / 2)
        nazlk = int(azimuth_spacing / 2)
        rstep = int(range_spacing)
        zstep = int(azimuth_spacing)
        i_fid.write(f'{interf_bin} {ref_slc} {sec_slc} {ref_par} {sec_par} '
                    f'{offsets_par} {offsets} {ref_pwr1} {sec_par1} '
                    f'{intef_path} {nrlk} {nazlk} {rstep} {zstep}')

    # - Change access permissions to the bash script
    os.chmod(bat_inter_path, 0o777)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="""Compute Dense Offset Map - AMPCOR."""
    )
    parser.add_argument('reference', type=str,  help='Reference SLC.')

    parser.add_argument('secondary', type=str, help='Secondary SLC.')

    parser.add_argument('--directory', '-D', help='Data directory.',
                        default=os.getcwd())

    parser.add_argument('--out_directory', '-O', help='Output directory.',
                        default=os.getcwd())

    parser.add_argument('--search_w', '-W', help='Search Window.',
                        type=int, default=64)

    parser.add_argument('--skip', '-S', help='Skip - Def: Search Window/2.',
                        type=int, default=None)

    parser.add_argument('--interp_off', help='Interpolate Offset Map to a '
                                             'different resolution.',
                        action='store_true')

    parser.add_argument('--out_off_spacing',
                        help='Offset Map Range/Azimuth Spacing.',
                        default=None, type=int)

    parser.add_argument('--off_weight', help='Offsets polynomial weight.',
                        type=str, default='ccp', choices=['ccp', 'snr'])

    parser.add_argument('--off_filter', help='Offsets filtering strategy.',
                        type=int, default=1, choices=[1, 2])

    parser.add_argument('--off_smooth', help='Smooth offsets map.',
                        action='store_true')

    parser.add_argument('--off_fill', help='Fill offsets map.',
                        action='store_true')

    parser.add_argument('--resample_azimuth',
                        help='Resample Secondary - Update Azimuth Resolution',
                        action='store_true')

    parser.add_argument('--resample_slc_prf',
                        help='Resample Secondary - Update Secondary PRF.',
                        action='store_true')

    parser.add_argument('--intf', help='Setup Interferogram Calculation.',
                        action='store_true')

    args = parser.parse_args()

    # - Path to Test directory
    data_dir = args.directory       # - Path to data directory
    out_dir = args.out_directory    # - Path to output directory

    # - Processing Parameters
    ref = args.reference            # - Reference SLC
    sec = args.secondary            # - Secondary SLC
    pair_name = f'{ref}-{sec}'        # - Pair name
    poly_order = 3      # - Polynomial order for offset estimation

    # - Generate new offset file
    algorithm = 1       # - offset estimation algorithm
    rlks = 1  # - number of interferogram range looks (enter -  for default: 1)
    azlks = 1  # - number of interferogram azimuth looks (enter-for default: 1)
    iflg = 0  # -  interactive mode flag (enter -  for default)

    # - Create Offset Parameter File
    print('#  - Create Offset Parameter File')
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

    # - Normalize SLCs Azimuth Resolution
    if args.resample_azimuth and args.resample_slc_prf:
        raise ValueError('Select a single resampling method.')

    if args.resample_azimuth:
        print('#  - Resample Secondary SLCs')
        print('#  - Update SLCs Azimuth Resolution')
        resample_slc_azimuth(data_dir, ref, sec, multi_look=False)
        sec = args.secondary+'_r'   # - Secondary SLC
        pair_name = f'{ref}-{sec}'  # - Pair name

    if args.resample_slc_prf:
        print('#  - Resample Secondary SLCs')
        print('#  - Update SLCs PRF')
        resample_slc_prf(data_dir, ref, sec, multi_look=False)
        sec = args.secondary+'_r'   # - Secondary SLC
        pair_name = f'{ref}-{sec}'  # - Pair name

    # - Set Skip Value equal to half of Search Window
    if args.skip is None:
        args.skip = args.search_w // 2

    # - Offsets Processing Parameters
    filter_strategy = args.off_filter       # - Offsets Filtering Strategy
    smooth_off = args.off_smooth            # - Smooth Offsets Map
    fill_off = args.off_fill                # - Fill Offsets Map

    # - Estimates the range and azimuth registration offset fields
    # - on a preliminary coarse resolution grid
    print('#  - Estimate the range and azimuth offset fields.')
    c_search_w = args.search_w
    c_skip = args.skip
    print(f'#  - Search Window: {c_search_w}, Skip: {c_skip}\n')
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
    o_rn = np.array(o_rn/rn_spacing, dtype=int)
    o_az = np.array(o_az/az_spacing, dtype=int)

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
        os.path.join(out_dir, f'{pair_name}.offmap.{args.off_weight}'),
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
               rn_smp,  '-', '-', '-', '-', '-', '-', '-',
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
        med_filt_size = 9   # - Median filter Kernel Size
        med_thresh = 1      # - Median filter Threshold
    elif filter_strategy == 2:
        # - Filtering Strategy 2 - see c_off3intf.pro
        med_filt_size = 15   # - Median filter Kernel Size
        med_thresh = 0.5     # - Median filter Threshold
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

    if args.intf:
        offsets = os.path.join(out_dir, f'{pair_name}_doffs_noramp_smooth')
        offsets_par = os.path.join(out_dir, f'{pair_name}.par')
        setup_intf(data_dir, ref, sec, offsets, offsets_par,
                   args.skip, args.skip)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
