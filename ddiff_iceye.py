#!/usr/bin/env python
u"""
Enrico Ciraci' - 03/2022

Compute Double-Difference Interferogram from ICEYE data.
- Use data expressed in RADAR Coordinates.

PYTHON DEPENDENCIES:
    argparse: Parser for command-line options, arguments and sub-commands
           https://docs.python.org/3/library/argparse.html
    numpy: The fundamental package for scientific computing with Python
          https://numpy.org/
    matplotlib: Visualization with Python
        https://matplotlib.org/
    tqdm: Progress Bar in Python.
          https://tqdm.github.io/
    datetime: Basic date and time types
           https://docs.python.org/3/library/datetime.html#module-datetime

    py_gamma: GAMMA's Python integration with the py_gamma module

UPDATE HISTORY:

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
from utils.read_keyword import read_keyword


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
    default_dir = os.environ['PYTHONDATA']
    parser.add_argument('--directory', '-D',
                        type=lambda p: os.path.abspath(
                            os.path.expanduser(p)),
                        default=default_dir,
                        help='Project data directory.')

    parser.add_argument('--init_offset', '-I', action='store_true',
                        help='Determine initial offset between SLC'
                             'images using correlation of image intensity')

    args = parser.parse_args()

    # - Path to data dir
    igram_ref = args.reference
    igram_sec = args.secondary
    if args.init_offset:
        data_dir_ref = os.path.join(args.directory, 'pair_diff_io', igram_ref)
        data_dir_sec = os.path.join(args.directory, 'pair_diff_io', igram_sec)
    else:
        data_dir_ref = os.path.join(args.directory, 'pair_diff', igram_ref)
        data_dir_sec = os.path.join(args.directory, 'pair_diff', igram_sec)

    # - Verify that the selected interferograms exist
    if not os.path.isdir(data_dir_ref):
        print(f'# - {data_dir_ref} - Not Found.')
        sys.exit()
    if not os.path.isdir(data_dir_sec):
        print(f'# - {data_dir_sec} - Not Found.')
        sys.exit()

    # - Path to Interferogram Parameter Files
    ref_par = os.path.join(data_dir_ref, igram_ref+'.offmap.par.interp')
    sec_par = os.path.join(data_dir_sec, igram_sec+'.offmap.par.interp')

    # - read reference interferogram parameter file
    ref_par_dict = pg.ParFile(ref_par).par_dict
    # - Interferogram Width
    ref_interf_width = int(ref_par_dict['interferogram_width'][0])

    # - Reference SLCs for the selected interferograms
    ref_pair_ref = os.path.join(data_dir_ref, igram_ref.split('-')[0])
    ref_pair_sec = os.path.join(data_dir_sec, igram_sec.split('-')[0])
    
    # - Interferograms
    ref_interf = os.path.join(data_dir_ref,
                              'coco' + igram_ref + '.flat.topo_off')
    ref_pwr = os.path.join(data_dir_ref, igram_ref.split('-')[0] + '.pwr1')
    ref_pwr_geo = os.path.join(data_dir_ref,
                               igram_ref.split('-')[0] + '.pwr1.geo')
    # -
    sec_interf = os.path.join(data_dir_sec,
                              'coco' + igram_sec + '.flat.topo_off')
    sec_pwr = os.path.join(data_dir_sec, igram_sec.split('-')[0] + '.pwr1')

    # - Path to Interferograms Baseline Files
    ref_base = os.path.join(data_dir_ref, 'base' + igram_ref + '.dat')
    sec_base = os.path.join(data_dir_sec, 'base' + igram_sec + '.dat')

    # - Create Output Directory
    if args.init_offset:
        out_dir = make_dir(args.directory, 'ddiff_io')
    else:
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
                   str(sec_interf.split('/')[-1]) + '.reg',
                   1, 1)
    pg.interp_data(sec_pwr, diff_par,
                   str(sec_pwr.split('/')[-1]).replace('.pwr1', '.reg.pwr1'),
                   0, 1)

    # - path to co-registered complex interferogram
    reg_intf = str(sec_interf.split('/')[-1]) + '.reg'
    # - Combine Complex Interferograms
    pg.comb_interfs(ref_interf, reg_intf, ref_base, sec_base, 1, -1,
                    ref_interf_width,
                    'coco' + igram_ref + '-' + igram_sec + '.flat.topo_off',
                    'base' + igram_ref + '-' + igram_sec + '.flat.topo_off',

                    )
    # - Read Double Difference Parameter file
    pg.rasmph_pwr('coco' + igram_ref + '-' + igram_sec + '.flat.topo_off',
                  ref_pwr, ref_interf_width)

    # - Smooth the obtained interferogram with pg.adf
    # - Adaptive interferogram filter using the power spectral density.
    pg.adf('coco' + igram_ref + '-' + igram_sec + '.flat.topo_off',
           'coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.filt',
           'coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.filt.coh',
           ref_interf_width)
    pg.rasmph_pwr('coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.filt',
                  ref_pwr, ref_interf_width)

    # - Geocode Double Difference
    # -  Reference Interferogram look-up table
    ref_gcmap = os.path.join(data_dir_ref, 'gc_icemap')
    dem_par_path = os.path.join(data_dir_ref, 'DEM_gc_par')
    try:
        dem_param_dict = pg.ParFile(dem_par_path).par_dict
        dem_width = int(dem_param_dict['width'][0])
        dem_nlines = int(dem_param_dict['nlines'][0])
    except IndexError:
        dem_width = int(read_keyword(dem_par_path, 'width'))
        dem_nlines = int(read_keyword(dem_par_path, 'nlines'))

    pg.geocode_back('coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.filt',
                    ref_interf_width,
                    ref_gcmap,
                    'coco' + igram_ref + '-' + igram_sec
                    + '.flat.topo_off.filt.geo',
                    dem_width, dem_nlines,
                    '-', 1
                    )
    pg.rasmph_pwr('coco' + igram_ref + '-' + igram_sec
                  + '.flat.topo_off.filt.geo',
                  ref_pwr_geo, dem_width)

    # - Calculate real part, imaginary part, intensity, magnitude,
    # - or phase of FCOMPLEX data
    # - Extract Interferogram Phase.
    pg.cpx_to_real('coco' + igram_ref + '-' + igram_sec
                   + '.flat.topo_off.filt.geo',
                   'phs.geo', dem_width, 4)
    pg.raspwr('phs.geo', dem_width)
    # - Save Geocoded Interferogram phase as a GeoTiff
    pg.data2geotiff(dem_par_path, 'phs.geo', 2,
                    'coco' + igram_ref + '-' + igram_sec
                    + '.flat.topo_off.filt.geo.tiff', -9999)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print("# - Computation Time: {}".format(end_time - start_time))
