#!/usr/bin/env python
u"""
compute_offsets.py

Written by Enrico Ciraci' (10/2021)

Calculate Preliminary Offsets Parameter File for a pair of ICEye Single Look
Complex images using  GAMMA's Python integration with the py_gamma module.

usage: compute_offsets.py [-h] [--directory DIRECTORY] reference secondary

Calculate Preliminary Offsets Parameter.

positional arguments:
  reference             Reference SLCs.
  secondary             Secondary SLCs.

options:
  -h, --help            show this help message and exit
  --directory DIRECTORY, -D DIRECTORY
                        Project data directory.
  --init_offset, -I     Determine initial offset between SLCimages using
                        correlation of image intensity
  --resample_azimuth    Resample Secondary - Update Azimuth Resolution
  --resample_slc_prf    Resample Secondary - Update Secondary PRF.



PYTHON DEPENDENCIES:
    argparse: Parser for command-line options, arguments and sub-commands
           https://docs.python.org/3/library/argparse.html
    datetime: Basic date and time types
           https://docs.python.org/3/library/datetime.html#module-datetime
    tqdm: Progress Bar in Python.
          https://tqdm.github.io/
    py_gamma: GAMMA's Python integration with the py_gamma module

UPDATE HISTORY:
    06/22/2022 - Directory parameter converted to positional argument.
        By default, the current directory is used as working directory.
    12/29/2022 - resample_azimuth/resample_slc_prf options added.

"""
# - Python Dependencies
from __future__ import print_function
import os
import argparse
import datetime
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
# - st_release
from st_release.resample_slc import resample_slc_azimuth, resample_slc_prf


def main() -> None:
    parser = argparse.ArgumentParser(
        description="""Calculate Preliminary Offsets Parameter."""
    )
    # - Absolute Path to directory containing input data.
    parser.add_argument('reference', type=str,
                        help='Reference SLCs.')

    parser.add_argument('secondary', type=str,
                        help='Secondary SLCs.')

    parser.add_argument('--directory', '-D',  help='Data directory.',
                        default=os.getcwd())

    parser.add_argument('--out_directory', '-O', help='Output directory.',
                        default=os.getcwd())

    parser.add_argument('--init_offset', '-I', action='store_true',
                        help='Determine initial offset between SLC'
                             'images using correlation of image intensity')

    parser.add_argument('--resample_azimuth',
                        help='Resample Secondary - Update Azimuth Resolution',
                        action='store_true')

    parser.add_argument('--resample_slc_prf',
                        help='Resample Secondary - Update Secondary PRF.',
                        action='store_true')

    args = parser.parse_args()

    # - Path to Test directory
    data_dir = args.directory
    out_dir = args.out_directory

    # - Parameters
    ref = args.reference    # Reference SLC
    sec = args.secondary    # Secondary SLC

    # - Offset Computation parameter
    algorithm = 1       # - offset estimation algorithm
    rlks = 1   # - number of interferogram range looks (enter -  for default: 1)
    azlks = 1   # - number of interferogram azimuth looks (enter-for default: 1)
    iflg = 0   # -  interactive mode flag (enter -  for default)

    # - init_offset - Parameters
    # - center of patch (enter - for default: image center)
    rpos = '-'   # - center of patch in range (samples)
    azpos = '-'  # - center of patch in azimuth (lines)
    offr = '-'  # - initial range offset (samples) (enter - for default: 0)
    offaz = '-'  # - initial azimuth offset (lines) (enter - for default: 0)
    thres = '-'  # - cross-correlation threshold (enter - for default: 0.150)
    rwin = 512   # - range window size (default: 512)
    azwin = 512  # - azimuth window size (default: 512)

    # - Output directory name
    out_name = ref + '-' + sec

    # - output parameter file
    out_par = os.path.join(out_dir, out_name + '.par')

    # - Create Offset Parameter File
    pg.create_offset(os.path.join(data_dir, ref+'.par'),
                     os.path.join(data_dir, sec+'.par'), out_par,
                     algorithm, rlks, azlks, iflg)

    # - Initial SLC image offset estimation from orbit state-vectors
    # - and image parameters
    pg.init_offset_orbit(os.path.join(data_dir, ref+'.par'),
                         os.path.join(data_dir, sec+'.par'), out_par)

    # - Determine initial offset between SLC images using correlation
    # - of image intensity
    if args.init_offset:
        pg.init_offset(os.path.join(data_dir, ref+'.slc'),
                       os.path.join(data_dir, sec+'.slc'),
                       os.path.join(data_dir, ref+'.par'),
                       os.path.join(data_dir, sec+'.par'),
                       out_par, rlks, azlks, rpos, azpos, offr, offaz,
                       thres, rwin, azwin)

    # - Create symbolic links for each of the .slc and .par files
    if out_dir != data_dir:
        if os.path.isfile(os.path.join(out_dir, ref+'.slc')):
            os.remove(os.path.join(out_dir, ref+'.slc'))
        os.symlink(os.path.join(data_dir, ref+'.slc'),
                   os.path.join(out_dir, ref+'.slc'))
        # -
        if os.path.isfile(os.path.join(out_dir, ref+'.par')):
            os.remove(os.path.join(out_dir, ref+'.par'))
        os.symlink(os.path.join(data_dir, ref+'.par'),
                   os.path.join(out_dir, ref+'.par'))
        # -
        if os.path.isfile(os.path.join(out_dir, sec+'.slc')):
            os.remove(os.path.join(out_dir, sec+'.slc'))
        os.symlink(os.path.join(data_dir, sec+'.slc'),
                   os.path.join(out_dir, sec+'.slc'))
        # -
        if os.path.isfile(os.path.join(out_dir, sec+'.par')):
            os.remove(os.path.join(out_dir, sec+'.par'))
        os.symlink(os.path.join(data_dir, sec+'.par'),
                   os.path.join(out_dir, sec+'.par'))

    # - if selected Normalize SLCs Azimuth Resolution
    if args.resample_azimuth and args.resample_slc_prf:
        raise ValueError('Select a single resampling method.')

    if args.resample_azimuth:
        print('#  - Resample Secondary SLCs')
        print('#  - Update SLCs Azimuth Resolution')
        resample_slc_azimuth(out_dir, ref, sec, multi_look=True)

    if args.resample_slc_prf:
        print('#  - Resample Secondary SLCs')
        print('#  - Update SLCs PRF')
        resample_slc_prf(out_dir, ref, sec, multi_look=True)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
