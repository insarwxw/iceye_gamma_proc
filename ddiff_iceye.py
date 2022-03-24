"""
Enrico Ciraci' - 03/2022

Compute Double-Difference Interferogram from ICEYE data.
"""
# - Python dependencies
from __future__ import print_function
import os
import sys
import shutil
import argparse
import datetime
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
from utils.make_dir import make_dir


def main():
    # - Read the system arguments listed after the program
    parser = argparse.ArgumentParser(
        description="""Compute Double-Difference Interferogram between the
        selected pair of interferograms.
        """
    )
    # - Positional Arguments - Reference and Secondary SLCs.
    parser.add_argument('reference', type=str, default=None,
                        help='Reference Interferogram')
    parser.add_argument('secondary', type=str, default=None,
                        help='Secondary Interferogram')

    # - Working Directory directory.
    default_dir = os.path.join(os.path.expanduser('~'), 'Desktop',
                               'iceye_gamma_test', 'output')
    parser.add_argument('--directory', '-D',
                        type=lambda p: os.path.abspath(
                            os.path.expanduser(p)),
                        default=default_dir,
                        help='Project data directory.')

    args = parser.parse_args()

    # - Path to data dir
    igram_ref = args.reference
    igram_sec = args.secondary
    data_dir_ref = os.path.join(args.directory, 'pair_diff', igram_ref)
    data_dir_sec = os.path.join(args.directory, 'pair_diff', igram_sec)

    # - Verify that the selected interferograms exist
    if not os.path.isdir(data_dir_ref):
        print(f'# - {data_dir_ref} - Not Found.')
        sys.exit()
    if not os.path.isdir(data_dir_sec):
        print(f'# - {data_dir_sec} - Not Found.')
        sys.exit()

    # - Path Interferogram Parameter Files
    ref_par = os.path.join(data_dir_ref, igram_ref+'.offmap.par.interp')
    sec_par = os.path.join(data_dir_sec, igram_sec+'.offmap.par.interp')

    # - Reference SLCs both interferograms
    ref_pair_ref = os.path.join(data_dir_ref, igram_ref.split('-')[0])
    ref_pair_sec = os.path.join(data_dir_sec, igram_sec.split('-')[0])
    
    # - Interferograms
    ref_interf = os.path.join(data_dir_ref,
                              'coco' + igram_ref + '.flat.topo_off')
    sec_interf = os.path.join(data_dir_sec,
                              'coco' + igram_sec + '.flat.topo_off')
    sec_pwr = os.path.join(data_dir_sec, igram_sec.split('-')[0] + '.pwr1')

    # - Create Output Directory
    out_dir = make_dir(args.directory, 'ddiff')
    out_dir = make_dir(out_dir, igram_ref + '--' + igram_sec)
    # Change the current working directory
    os.chdir(out_dir)

    # - Create Double Difference Parameter File
    diff_par = 'DIFF_par' + igram_ref + '--' + igram_sec
    pg.create_diff_par(ref_par, sec_par, diff_par, 0, 0)
    # - Estimate Initial Offset
    pg.init_offsetm(ref_pair_ref+'.pwr1', ref_pair_sec + '.pwr1',
                    diff_par, 1, 1, '-', '-', '0', '0', '-', '-', 1)

    # - Starting Double Difference Computation: Orbits based
    pg.create_offset(ref_pair_ref + '.par',
                     ref_pair_sec + '.par',
                     igram_ref.split('-')[0] + '-' + igram_sec.split('-')[0]
                     + '.par', 1, 15, 15, 0
                     )
    pg.init_offset_orbit(ref_pair_ref + '.par',
                         ref_pair_sec + '.par',
                         igram_ref.split('-')[0] + '-' + igram_sec.split('-')[0]
                         + '.par', '-', '-', 1
                         )

    # - Interpolate Secondary interferogram on the Reference Grid
    pg.interp_data(sec_interf, diff_par,
                   sec_interf.split('/')[-1] + '.reg',
                   1, 1)
    pg.interp_data(sec_pwr, diff_par,
                   sec_pwr.split('/')[-1].replace('.pwr1', '.reg.pwr1'),
                   0, 1)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print("# - Computation Time: {}".format(end_time - start_time))