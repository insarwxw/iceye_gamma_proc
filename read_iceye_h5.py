#!/usr/bin/env python
u"""
read_iceye_h5.py
Written by Enrico Ciraci' (03/2022)
Read ICEye Single Look Complex and Parameter file using  GAMMA's Python
integration with the py_gamma module.

usage: read_iceye_h5.py [-h] [--directory DIRECTORY]

TEST: Read ICEye Single Look Complex and Parameter.

optional arguments:
  -h, --help            show this help message and exit
  --directory DIRECTORY, -D DIRECTORY
                        Project data directory.
  --slc SLC, -C SLC     Process and single SLC.

PYTHON DEPENDENCIES:
    argparse: Parser for command-line options, arguments and sub-commands
           https://docs.python.org/3/library/argparse.html
    datetime: Basic date and time types
           https://docs.python.org/3/library/datetime.html#module-datetime
    tqdm: Progress Bar in Python.
          https://tqdm.github.io/

UPDATE HISTORY:

"""
# - Python Dependencies
from __future__ import print_function
import os
import argparse
import datetime
from tqdm import tqdm
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
from utils.make_dir import make_dir


def main():
    parser = argparse.ArgumentParser(
        description="""TEST: Read ICEye Single Look Complex and Parameter."""
    )
    # - Absolute Path to directory containing input data.
    default_dir = os.path.join(os.path.expanduser('~'), 'Desktop',
                               'iceye_gamma_test')
    parser.add_argument('--directory', '-D',
                        type=lambda p: os.path.abspath(os.path.expanduser(p)),
                        default=default_dir,
                        help='Project data directory.')

    parser.add_argument('--slc', '-C', type=str,
                        default=None, help='Process and single SLC.')

    args = parser.parse_args()

    # - Path to Test directory
    data_dir = os.path.join(args.directory, 'input')

    # - create output directory
    out_dir = make_dir(args.directory, 'output')
    out_dir = make_dir(out_dir, 'slc+par')

    # - ICEye Suffix
    ieye_suff = 'ICEYE_X7_SLC_SM_'

    if args.slc is not None:
        # - Process a single SLC
        b_input = os.path.join(args.directory, args.slc)
        # - Read input Binary File Name
        b_input_name = b_input.split('/')[-1].replace(ieye_suff, '')
        slc_name = os.path.join(out_dir,
                                str(b_input_name.replace('.h5', '.slc')))
        par_name = os.path.join(out_dir,
                                str(b_input_name.replace('.h5', '.par')))
        # - Extract SLC and Parameter File
        # - Set dtype equal to zero to save the SLC in FCOMPLEX format.
        pg.par_ICEYE_SLC(b_input, par_name, slc_name, 0)

    else:
        # - Process hte entire input directory content
        # - List Directory Content
        data_dir_list = [os.path.join(data_dir, x) for x in os.listdir(data_dir)
                         if x.endswith('.h5')]

        for b_input in tqdm(data_dir_list, total=len(data_dir_list), ncols=60):
            # - Read input Binary File Name
            b_input_name = b_input.split('/')[-1].replace(ieye_suff, '')
            slc_name = os.path.join(out_dir, b_input_name.replace('.h5', '.slc'))
            par_name = os.path.join(out_dir, b_input_name.replace('.h5', '.par'))
            # - Extract SLC and Parameter File
            # - Set dtype equal to zero to save the SLC in FCOMPLEX format.
            pg.par_ICEYE_SLC(b_input, par_name, slc_name, 0)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
