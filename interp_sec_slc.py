#!/usr/bin/env python
u"""
Enrico Ciraci' - 01/2023

Interpolate Secondary SLC to the Reference SLC using third order polynomial
computer Range and Azimuth Preliminary Offsets field.


usage: interp_sec_slc.py [-h] [--directory DIRECTORY]
    [--out_directory OUT_DIRECTORY] [--pdoff] reference secondary

positional arguments:
  reference             Reference SLC.
  secondary             Secondary SLC.

options:
  -h, --help            show this help message and exit
  --directory DIRECTORY, -D DIRECTORY
                        Data directory.
  --out_directory OUT_DIRECTORY, -O OUT_DIRECTORY
                        Output directory.
  --pdoff, -p           Compute preliminary dense offsets field.


"""
# - Python Dependencies
from __future__ import print_function
import os
import argparse
import datetime
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="""Interpolate Secondary SLC to the Reference SLC using
        third order polynomial computer Range and Azimuth Preliminary Offsets
        field.
        """
    )
    parser.add_argument('reference', type=str, help='Reference SLC.')

    parser.add_argument('secondary', type=str, help='Secondary SLC.')

    parser.add_argument('--directory', '-D', help='Data directory.',
                        default=os.getcwd())

    parser.add_argument('--out_directory', '-O', help='Output directory.',
                        default=os.getcwd())

    parser.add_argument('--pdoff', '-p',
                        help='Compute preliminary dense offsets field.',
                        action='store_true')

    args = parser.parse_args()

    # - Path to Test directory
    data_dir = args.directory  # - Path to data directory
    out_dir = args.out_directory  # - Path to output directory

    # - Processing Parameters
    ref = args.reference  # - Reference SLC
    sec = args.secondary  # - Secondary SLC

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
                      64, 64, os.path.join(data_dir, f'sparse_offsets.txt'),
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


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
