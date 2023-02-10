#!/usr/bin/env python
# - Python Dependencies
from __future__ import print_function
import os
import argparse
import datetime
from tqdm import tqdm
import subprocess
from multiprocessing import Pool
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
import py_gamma2019 as pg9
# - Package Dependencies
from c_ampcor_iceye import c_ampcor_iceye
from interp_sec_slc import register_slc


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


def run_sub_process(cmd: str) -> None:
    """
    Run a command in a subprocess
    :param cmd: command to run
    :return: None
    """
    # - Run the command
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(cmd,
                              stdout=devnull,
                              stderr=subprocess.STDOUT)


def main() -> None:
    # - Read the system arguments listed after the program
    parser = argparse.ArgumentParser(
        description="""Run Interferometric Processing (ISP) on a pair of SLCs."""
    )
    # - Reference SLCs
    parser.add_argument('ref_slc', type=str,
                        help='Reference SLCs.')
    # - Secondary SLCs
    parser.add_argument('sec_slc', type=str,
                        help='Secondary SLCs.')
    # - Data Directory
    parser.add_argument('--directory', '-D',
                        help='Data directory.',
                        default=os.getcwd())
    # - Output Directory
    parser.add_argument('--out_directory', '-O', help='Output directory.',
                        default=os.getcwd())

    # - Number of Parallel Processes
    parser.add_argument('--n_proc', '-N',
                        type=int, default=15,
                        help='Number of Parallel Processes.')

    # - AMPCOR Binary Selected
    parser.add_argument('--ampcor', '-A',
                        type=str, default='ampcor_large',
                        choices=['ampcor_large', 'ampcor_large2',
                                 'ampcor_superlarge2'],
                        help='AMPCOR Binary Selected.')

    # - Register SLCs using 3rd order polynomial
    # - Obtained by computing preliminary dense offsets field
    parser.add_argument('--pdoff', '-p',
                        help='Compute preliminary dense offsets field.',
                        action='store_true')

    args = parser.parse_args()

    # - Read input parameters
    ref_slc = args.ref_slc      # - Reference SLC
    sec_slc = args.sec_slc      # - Secondary SLC
    data_dir = args.directory   # - Data directory
    out_dir = args.out_directory    # - Output directory
    n_proc = args.n_proc    # - Number of parallel processes
    ampcor_bin = args.ampcor    # - AMPCOR binary selected
    pdoff = args.pdoff         # - Compute preliminary dense offsets field

    # - Register SLC-2 to SLC-1 using 3rd order polynomial
    # register_slc(ref_slc, sec_slc,  # - Reference and Secondary SLC
    #              pdoff=pdoff,       # - Compute preliminary dense offsets field
    #              data_dir=data_dir,     # - Path to data directory
    #              out_dir=out_dir)       # - Path to output directory

    # - Create the bat file to run AMPCOR
    sec_slc = f'{sec_slc}.reg'  # - Secondary SLC registered to reference SLC
    c_ampcor_iceye(ref_slc, sec_slc,    # - Reference and Secondary SLC
                   data_dir=data_dir,   # - Path to data directory
                   out_dir=out_dir,     # - Path to output directory
                   n_proc=n_proc,       # - Number of parallel processes
                   ampcor=ampcor_bin)   # - AMPCOR binary selected

    print('# - Run AMPCOR.')
    # - Read ampcor bat file
    with open(os.path.join(out_dir, f'bat_{ref_slc}-{sec_slc}')) as r_fid:
        sub_proc = r_fid.readlines()
    sub_proc_list = [s.split(' ')[0:2] for s in sub_proc]

    # - Run AMPCOR
    with Pool(n_proc) as p:
        p.map(run_sub_process, sub_proc_list)

    print('# - AMPCOR Run Completed.')


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
