"""
Calculate a multi-look intensity (MLI) image from ICEye Single Look Complex
using  GAMMA's Python integration with the py_gamma module.
"""
# - Python Dependencies
from __future__ import print_function
import os
import argparse
import datetime
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg


def main():
    parser = argparse.ArgumentParser(
        description="""TEST: Calculate a multi-look intensity (MLI)
        image from ICEye SLCs."""
    )
    # - Absolute Path to directory containing input data.
    default_dir = os.path.join(os.path.expanduser('~'), 'Desktop',
                               'iceye_gamma_test', 'output', 'slc+par')
    parser.add_argument('--directory', '-D',
                        type=lambda p: os.path.abspath(os.path.expanduser(p)),
                        default=default_dir,
                        help='Project data directory.')

    args = parser.parse_args()

    # - Path to Test directory
    data_dir = args.directory

    # - Parameters
    rlks = 10          # - number of range looks (INT)
    azlks = 5          # - number of azimuth looks (INT)
    raspwr_f = True    # - save power amplitude image raster

    # - List Directory Content
    data_dir_list = [os.path.join(data_dir, x) for x in os.listdir(data_dir)
                     if x.endswith('.slc')]

    for b_input in data_dir_list:
        # - Read input Binary File Name
        b_input_name = b_input.split('/')[-1]
        slc_name = os.path.join(data_dir, b_input_name)
        par_name = os.path.join(data_dir, b_input_name.replace('.slc', '.par'))
        mli_name = os.path.join(data_dir, b_input_name.replace('.slc', '.mli'))
        mli_par_name = os.path.join(data_dir,
                                    b_input_name.replace('.slc', '.mli.par'))
        # - Extract SLC and Parameter File
        pg.multi_look(slc_name, par_name, mli_name, mli_par_name, rlks, azlks)

        # - Read Multi-Looked SLCs par file
        par_dict = pg.ParFile(mli_par_name).par_dict
        n_rsmpl = int(par_dict['range_samples'][0])
        print(n_rsmpl)
        print(mli_name)
        if raspwr_f:
            # - Calculate a raster image from data with power-law scaling
            pg.raspwr(mli_name, n_rsmpl)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
