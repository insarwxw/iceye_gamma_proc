#!/usr/bin/env python
u"""
Enrico Ciraci' - 01/2023

usage: resample_slc.py [-h] [--slc SLC] [--directory DIRECTORY]
        [--out_directory OUT_DIRECTORY] prf


Resample the input SLC at the selected Azimuth Resolution and PRF

positional arguments:
  prf                   output PRF.

options:
  -h, --help            show this help message and exit
  --slc SLC, -S SLC     Process a single SLC.
  --directory DIRECTORY, -D DIRECTORY
                        Data directory.

  --out_directory OUT_DIRECTORY, -O OUT_DIRECTORY
                        Output directory.

"""
# - Python Dependencies
from __future__ import print_function
import os
import argparse
import datetime
import numpy as np
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg


def main() -> None:
    parser = argparse.ArgumentParser(
        description="""Resample the input SLC at the selected Azimuth
        Resolution and PRF"""
    )

    parser.add_argument('prf', type=float,  help='output PRF [Hz].')

    parser.add_argument('--slc', '-S', type=str,
                        default=None, help='Process a single SLC.')

    parser.add_argument('--directory', '-D', help='Data directory.',
                        default=os.getcwd())

    parser.add_argument('--out_directory', '-O', help='Output directory.',
                        default=os.getcwd())

    args = parser.parse_args()

    # - Path to Test directory
    prf = args.prf                  # - Output SLC's PRF
    data_dir = args.directory       # - Path to data directory
    out_dir = args.out_directory    # - Path to output directory

    if args.slc is not None:
        slc_list = [args.slc]
    else:
        # - List Directory Content
        slc_list = [os.path.join(data_dir, x) for x in os.listdir(data_dir)
                    if x.endswith('.slc')]

    for slc in slc_list:
        slc_name = slc.replace('.slc', '')
        # - Read Reference SLC par file
        slc_param = pg.ParFile(os.path.join(data_dir, f'{slc_name}.par'))

        # - Get Secondary PRF value
        slc_az_prf = float(slc_param.get_value('prf')[0])
        # - other parameters
        start_time = float(slc_param.get_value('start_time')[0])
        end_time = float(slc_param.get_value('end_time')[0])
        azimuth_pixel_spacing \
            = float(slc_param.get_value('azimuth_pixel_spacing')[0])

        # - Generate resampled SLC parameters file
        # - Azimuth line time: time between SLC image lines
        # - in the resampled SLC [s]
        azimuth_line_time = 1 / prf
        # - New Azimuth pixel spacing [m]
        azimuth_pixel_spacing *= (slc_az_prf / prf)

        # - Compute time duration of the original SLC derived from
        # - the start_time and end_time and divide by the new azimuth
        # - line time [-]
        azimuth_lines \
            = np.ceil(((end_time - start_time) / azimuth_line_time)) + 1
        # - Update end_time and center_time
        center_time = start_time + (azimuth_line_time * (azimuth_lines / 2))
        end_time = start_time + (azimuth_line_time * azimuth_lines)

        # - Generate Resampled Secondary SLC values
        slc_param.set_value('prf', prf)
        slc_param.set_value('azimuth_pixel_spacing', azimuth_pixel_spacing)
        slc_param.set_value('azimuth_line_time', azimuth_line_time)
        slc_param.set_value('azimuth_lines', int(azimuth_lines))
        slc_param.set_value('center_time', center_time)
        slc_param.set_value('end_time', end_time)

        # - save new parameter file
        slc_param.write_par(os.path.join(out_dir, f'{slc_name}.rsmp.par'))
        # - add stater vectors to the new parameter file
        with open(os.path.join(data_dir, f'{slc_name}.par'), 'r') as s_fid:
            st_vl = s_fid.readlines()
        with open(os.path.join(out_dir, f'{slc_name}.rsmp.par'), 'a') as r_fid:
            for line in st_vl:
                if line.startswith('state_vector_position_') or \
                        line.startswith('state_vector_velocity_'):
                    r_fid.write(line)

        # - resample secondary SLC
        pg.resamp_image_par(
            os.path.join(data_dir, f'{slc_name}.slc'),
            os.path.join(data_dir, f'{slc_name}.par'),
            os.path.join(out_dir, f'{slc_name}.rsmp.par'),
            os.path.join(out_dir, f'{slc_name}.rsmp.slc'),
            6,  # - use default interpolation method Bspline [4] / Lanczos [6]
            1,  # - input/output data type - FCOMPLEX
            7,  # - interpolation function order
        )

        # - Change access permissions to output data
        os.chmod(os.path.join(out_dir, f'{slc_name}.rsmp.par'), 0o777)
        os.chmod(os.path.join(out_dir, f'{slc_name}.rsmp.slc'), 0o777)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
