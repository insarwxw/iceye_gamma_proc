"""
Read ICEye Single Look Complex and Parameter file using  GAMMA's Python
integration with the py_gamma module.
"""
# - Python Dependencies
from __future__ import print_function
import os
import argparse
import datetime
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
from utils.make_dir import make_dir


def main():
    parser = argparse.ArgumentParser(
        description="""TEST: Read ICEye Single Look Complex and Parameter."""
    )
    # - Absolute Path to directory containing input data.
    default_dir = os.path.join(os.path.expanduser('~'), 'Desktop',
                               'iceye_gamma_test', 'input')
    parser.add_argument('--directory', '-D',
                        type=lambda p: os.path.abspath(os.path.expanduser(p)),
                        default=default_dir,
                        help='Project data directory.')

    args = parser.parse_args()

    # - Path to Test directory
    data_dir = args.directory

    # - List Directory Content
    data_dir_list = [os.path.join(data_dir, x) for x in os.listdir(data_dir)
                     if x.endswith('.h5')]

    # - create output directory
    out_dir = make_dir(os.path.join(os.path.expanduser('~'), 'Desktop',
                                    'iceye_gamma_test'), 'output')
    out_dir = make_dir(out_dir, 'slc+par')

    for b_input in data_dir_list:
        # - Read input Binary File Name
        b_input_name = b_input.split('/')[-1]
        slc_name = os.path.join(out_dir, b_input_name.replace('.h5', '.slc'))
        par_name = os.path.join(out_dir, b_input_name.replace('.h5', '.par'))
        # - Extract SLC and Parameter File
        pg.par_ICEYE_SLC(b_input, par_name, slc_name)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
