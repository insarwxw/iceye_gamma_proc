#!/usr/bin/env python
u"""
process_offsets.py
Written by Enrico Ciraci' (11/2022)

Preliminary Python implementation of process_offsets.pro in Python.
"""
# - Python Dependencies
from __future__ import print_function
import os
import argparse
import datetime
# - ST_Release dependencies
from st_release.r_off_sar import r_off_sar
from st_release.c_off4intf import c_off4intf
from utils.make_dir import make_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process dense offsets generated by AMPCOR."
    )
    # - Reference Single Look Complex Image
    parser.add_argument('reference', type=str,
                        help='Reference SLCs.')
    # - Secondary Single Look Complex Image
    parser.add_argument('secondary', type=str,
                        help='Secondary SLCs.')
    # - Data Directory
    parser.add_argument('--directory', '-D',
                        help='Data directory.',
                        default=os.getcwd())

    args = parser.parse_args()

    ref_slc = args.reference
    sec_slc = args.secondary

    # - Pair's directory
    data_dir = args.directory

    # - Process offsets - Stack offset files
    r_off_sar(data_dir, ref_slc, sec_slc)

    # -
    c_off4intf(data_dir, ref_slc, sec_slc,
               range_spacing=30, azimuth_spacing=30,
               filter_strategy=2, fill=False,
               smooth=True)

    # - create Save directory
    make_dir(data_dir, 'Save')


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
