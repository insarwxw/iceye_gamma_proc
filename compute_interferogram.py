# - Python dependencies
from __future__ import print_function
import os
import sys
import argparse
import datetime
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg


def main():
    # - Read the system arguments listed after the program
    parser = argparse.ArgumentParser(
        description="""Compute Interferogram for the selected pair.
            """
    )
    # - Working Directory directory.
    default_dir = os.path.join(os.path.expanduser('~'), 'Desktop',
                               'iceye_gamma_test', 'output')
    parser.add_argument('--directory', '-D',
                        type=lambda p: os.path.abspath(
                            os.path.expanduser(p)),
                        default=default_dir,
                        help='Project data directory.')
    parser.add_argument('--pair', '-P',
                        type=str,
                        default=None,
                        help='SLC Pair Codes separated by "_" '
                             'reference-secondary')
    args = parser.parse_args()

    if args.pair is None:
        print('# - Provide selected SLC names as: --pair=Ref_Code_Sec_Code')
        sys.exit()

    # - Reference and Secondary SLCs
    slc_list = args.pair.split('-')
    ref_slc = slc_list[0]
    sec_slc = slc_list[1]

    # - Define Data directory
    data_dir = os.path.join(args.directory,
                            'pair_diff', ref_slc + '-' + sec_slc)

    # - Compute Interferogram Baseline Base on SLCs orbit state vectors
    print('# - Estimate baseline from orbit state vectors (base_orbit)')
    pg.base_orbit(os.path.join(data_dir, ref_slc+'.par'),
                  os.path.join(data_dir, sec_slc+'.par'),
                  os.path.join(data_dir, f'base{ref_slc}-{sec_slc}.dat'))

    # - Add Shebang line to bat file
    with open(os.path.join(data_dir,
                           f'bat_inter.{ref_slc}-{sec_slc}'), 'r') as b_fid:
        bat_lines = b_fid.readlines()
    with open(os.path.join(data_dir,
                           f'./bat_inter.{ref_slc}-{sec_slc}'), 'w') as b_fid:
        print('#!/bin/sh', file=b_fid)
        for f_line in bat_lines:
            print(f_line, file=b_fid)
    print('# - Compute Interferogram (./bat_inter_ref_slc-sec_scl).')
    # - Calculate Interferogram
    os.system(os.path.join(data_dir, f'./bat_inter.{ref_slc}-{sec_slc}'))


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print("# - Computation Time: {}".format(end_time - start_time))