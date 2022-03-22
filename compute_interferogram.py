"""
Enrico Ciraci' - 03/2022

Compute Interferogram for the selected pair.
"""
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

    # - Data directory
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
    # Change the current working directory
    os.chdir(data_dir)
    # - Calculate Interferogram
    # os.system(os.path.join('.', f'bat_inter.{ref_slc}-{sec_slc}'))
    print('# - Interferogram Calculation Completed.')
    # - read interferogram parameter file
    igram_par_path = os.path.join('.',
                                  f'{ref_slc}-{sec_slc}.offmap.par.interp')
    igram_param_dict = pg.ParFile(igram_par_path).par_dict
    # - read interferogram number of columns
    n_col = int(igram_param_dict['interferogram_width'][0])

    # - Generate 8-bit raster image of the interferogram
    # - plotted on top of the reference intensity image.
    print('# - Generate 8-bit raster image of the interferogram '
          'plotted on top of the reference SLC intensity image')
    pg.rasmph_pwr(os.path.join('.', f'coco{ref_slc}-{sec_slc}.dat'),
                  os.path.join('.', f'{ref_slc}.pwr1'), n_col)

    # - Remove Flat Earth Phase contribution to differential phase
    # - ph_slope_base -> Subtract/add interferogram Flat-Earth phase trend as
    # -                  estimated from initial baseline.
    # -                  See Gamma Remote Sensing.
    pg.ph_slope_base(f'coco{ref_slc}-{sec_slc}.dat',
                     f'{ref_slc}.par',
                     f'{ref_slc}-{sec_slc}.offmap.par.interp',
                     f'base{ref_slc}-{sec_slc}.dat',
                     f'coco{ref_slc}-{sec_slc}.flat')
    pg.rasmph_pwr(os.path.join('.', f'coco{ref_slc}-{sec_slc}.flat'),
                  os.path.join('.', f'{ref_slc}.pwr1'), n_col)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print("# - Computation Time: {}".format(end_time - start_time))
