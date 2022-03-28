#!/usr/bin/env python
u"""
compute_offsets.py

Calculate Preliminary Offsets Parameter File for a pair of ICEye Single Look
Complex images using  GAMMA's Python integration with the py_gamma module.

usage: compute_offsets.py [-h] [--directory DIRECTORY] reference secondary

Calculate Preliminary Offsets Parameter.

positional arguments:
  reference             Reference SLCs.
  secondary             Secondary SLCs.

optional arguments:
  -h, --help            show this help message and exit
  --directory DIRECTORY, -D DIRECTORY
                        Project data directory.

PYTHON DEPENDENCIES:
    argparse: Parser for command-line options, arguments and sub-commands
           https://docs.python.org/3/library/argparse.html
    datetime: Basic date and time types
           https://docs.python.org/3/library/datetime.html#module-datetime
    tqdm: Progress Bar in Python.
          https://tqdm.github.io/
    py_gamma: GAMMA's Python integration with the py_gamma module

UPDATE HISTORY:

"""
# - Python Dependencies
from __future__ import print_function
import os
import argparse
import datetime
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
from utils.make_dir import make_dir


def main():
    parser = argparse.ArgumentParser(
        description="""Calculate Preliminary Offsets Parameter."""
    )
    # - Absolute Path to directory containing input data.
    default_dir = os.path.join(os.path.expanduser('~'), 'Desktop',
                               'iceye_gamma_test', 'output')

    parser.add_argument('reference', type=str,
                        help='Reference SLCs.')

    parser.add_argument('secondary', type=str,
                        help='Secondary SLCs.')

    parser.add_argument('--directory', '-D',
                        type=lambda p: os.path.abspath(os.path.expanduser(p)),
                        default=default_dir,
                        help='Project data directory.')

    parser.add_argument('--init_offset', '-I', action='store_true', type=bool,
                        help='Determine initial offset between SLC'
                             'images using correlation of image intensity')

    args = parser.parse_args()

    # - Path to Test directory
    data_dir = os.path.join(args.directory, 'slc+par')

    # - Parameters
    ref = args.reference
    sec = args.secondary
    # - Ref/sec - possible combination
    # ref = '152307_20211022T145808'
    # sec = '152566_20211023T145809'

    # - Offset Computation parameter
    algorithm = 1       # - offset estimation algorithm
    rlks = 1   # - number of interferogram range looks (enter -  for default: 1)
    azlks = 1 # - number of interferogram azimuth looks (enter - for default: 1)
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
    out_dir_name = ref + '-' + sec

    # - Output Directory
    if args.init_offset:
        out_dir = make_dir(args.directory, 'pair_diff_io')
    else:
        out_dir = make_dir(args.directory, 'pair_diff')

    out_dir = make_dir(out_dir, out_dir_name)
    # - output parameter file
    out_par = os.path.join(out_dir, out_dir_name+'.par')

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


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
