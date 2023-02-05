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
import shutil
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
import py_gamma2019 as pg9
from utils.make_dir import make_dir


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
        c_skip = 32
        c_search_w = 64
        pg.offset_pwr_tracking(
            os.path.join(data_dir, f'{ref}.slc'),
            os.path.join(data_dir, f'{sec}.slc'),
            os.path.join(data_dir, f'{ref}.par'),
            os.path.join(data_dir, f'{sec}.par'),
            os.path.join(data_dir, f'{ref}-{sec}.par'),
            os.path.join(out_dir, f'sparse_offsets'),
            os.path.join(out_dir, f'sparse_offsets.ccp'),
            c_search_w, c_search_w,
            os.path.join(out_dir, f'sparse_offsets.txt'),
            '-', '-', c_skip, c_skip, '-', '-', '-', '-', '-', '-',
        )

        # - Read the offset parameter file
        off_param = pg.ParFile(os.path.join(data_dir, f'{ref}-{sec}.par'))
        rn_max = int(off_param.par_dict['offset_estimation_ending_range'][0])

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

            # - Update Offsets Parameter file
            off_param.set_value('offset_estimation_ending_range', rn_max)
            off_param.set_value('offset_estimation_ending_azimuth', az_max)
            off_param.set_value('offset_estimation_range_samples', rn_smp)
            off_param.set_value('offset_estimation_azimuth_samples', az_smp)
            off_param.set_value('offset_estimation_range_spacing', c_skip)
            off_param.set_value('offset_estimation_azimuth_spacing', c_skip)
            off_param.set_value('offset_estimation_window_width', c_search_w)
            off_param.set_value('offset_estimation_window_height', c_search_w)
            off_param.write_par(os.path.join(out_dir, f'{ref}-{sec}.par'))
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
    # - Run Gamma offset_sub: Subtraction of polynomial
    # - from range and azimuth offset estimates
    pg.offset_sub(
        os.path.join(data_dir, f'sparse_offsets'),
        os.path.join(data_dir, f'{ref}-{sec}.par'),
        os.path.join(data_dir, f'sparse_offsets.res'),
    )

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

    # - Save intermediate registration results inside a subdirectory
    reg_dir = make_dir(data_dir, 'slc_reg')
    shutil.move(os.path.join(data_dir, f'sparse_offsets'),
                os.path.join(reg_dir, f'sparse_offsets'))
    shutil.move(os.path.join(data_dir, f'sparse_offsets.res'),
                os.path.join(reg_dir, f'sparse_offsets.res'))
    shutil.move(os.path.join(data_dir, f'sparse_offsets.ccp'),
                os.path.join(reg_dir, f'sparse_offsets.ccp'))
    shutil.move(os.path.join(data_dir, f'sparse_offsets.txt'),
                os.path.join(reg_dir, f'sparse_offsets.txt'))
    # - Plot sparse offsets
    off_param = pg.ParFile(os.path.join(data_dir, f'{ref}-{sec}.par')).par_dict
    off_ncol = int(off_param['offset_estimation_range_samples'][0])
    pg9.rasmph(os.path.join(reg_dir, f'sparse_offsets.res'),
               off_ncol, '-', '-', '-', '-', '-', '-', '-',
               os.path.join(reg_dir, f'sparse_offsets.res.bmp'))


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
