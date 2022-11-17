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
from r_off_sar import r_off_sar
from c_off4intf import c_off4intf
from utils.make_dir import make_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="""Process outputs from AMPCOR and organize them 
        for interferogram calculation."""
    )
    # - Absolute Path to directory containing input data.
    parser.add_argument('directory', help='Project data directory.')

    parser.add_argument('reference', type=str,
                        help='Reference SLCs.')

    parser.add_argument('secondary', type=str,
                        help='Secondary SLCs.')

    args = parser.parse_args()

    ref_slc = args.reference
    sec_slc = args.secondary

    # - Pair's directory
    data_dir = os.path.join(args.directory, 'pair_diff',
                            ref_slc + '-' + sec_slc)
    # - move to data directory
    os.chdir(data_dir)

    # - Process offsets
    r_off_sar(ref_slc, sec_slc)
    # - Change access permission to preliminary outputs
    os.chmod('off.off', 0o777)
    c_off4intf(ref_slc, sec_slc, range_spacing=30, azimuth_spacing=30)

    # - create Save directory
    make_dir(data_dir, 'Save')


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
