#!/usr/bin/env python
u"""
Enrico Ciraci' - 01/2023

Compute Double-Difference Interferogram between the selected pair of
Geocoded Interferograms - GAMMA Pipeline.

usage: ddiff_iceye_geo_gamma.py [-h] input_yml

positional arguments:
  input_yml   Path to input yaml parameter file.

options:
  -h, --help  show this help message and exit


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
import argparse
import yaml
import datetime
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
import py_gamma2019 as pg9
from utils.make_dir import make_dir
from utils.read_keyword import read_keyword


def main() -> None:
    # - Read the system arguments listed after the program
    parser = argparse.ArgumentParser(
        description="""Compute Double-Difference Interferogram between the
        selected pair of Geocoded Interferograms - GAMMA Pipeline.
        """
    )
    # - Positional Arguments - Reference and Secondary SLCs.
    parser.add_argument('reference', type=str, default=None,
                        help='Reference Interferogram')

    parser.add_argument('secondary', type=str, default=None,
                        help='Secondary Interferogram')

    # - Positional Arguments - Reference and Secondary SLCs.
    parser.add_argument('input_yml', type=str, default=None,
                        help='Path to input yaml parameter file.')

    args = parser.parse_args()

    # - Read Processing Parameters
    processing_parameters_yml = os.path.join('.', args.input_yml)
    with open(processing_parameters_yml) as file:
        processing_parameters = yaml.load(file, Loader=yaml.FullLoader)

    # - Path to data dir
    data_dir = processing_parameters['directory']
    in_dir = processing_parameters['in_dir']
    out_dir = processing_parameters['out_dir']
    igram_ref = args.reference
    igram_sec = args.secondary
    data_dir_ref = os.path.join(data_dir, in_dir, igram_ref)
    data_dir_sec = os.path.join(data_dir, in_dir, igram_sec)

    # - Verify that the selected interferograms exist
    if not os.path.isdir(data_dir_ref):
        print(f'# - {data_dir_ref} - Not Found.')
        sys.exit()
    if not os.path.isdir(data_dir_sec):
        print(f'# - {data_dir_sec} - Not Found.')
        sys.exit()

    # - Path to Geocoded Interferogram Parameter Files
    ref_par = os.path.join(data_dir_ref, 'DEM_gc_par')
    sec_par = os.path.join(data_dir_sec, 'DEM_gc_par')

    try:
        dem_param_dict = pg.ParFile(ref_par).par_dict
        dem_width = int(dem_param_dict['width'][0])
    except IndexError:
        dem_width = int(read_keyword(ref_par, 'width'))

    # - Reference SLCs for the selected interferograms
    # ref_pair_ref = os.path.join(data_dir_ref, igram_ref.split('-')[0])
    # ref_pair_sec = os.path.join(data_dir_sec, igram_sec.split('-')[0])

    # - Geocoded Interferograms
    ref_interf \
        = os.path.join(data_dir_ref,
                       'coco' + igram_ref + '.reg2.intf.flat.topo_off.geo')
    sec_interf \
        = os.path.join(data_dir_sec,
                       'coco' + igram_sec + '.reg2.intf.flat.topo_off.geo')
    # - Geocoded Reference SLC Power Intensity
    ref_pwr \
        = os.path.join(data_dir_ref, igram_ref.split('-')[0]
                       + processing_parameters['pwr_suff'])

    # - Path to Interferograms Baseline Files
    ref_base \
        = os.path.join(data_dir_ref, 'base' + igram_ref + '.reg2.dat')
    sec_base\
        = os.path.join(data_dir_sec, 'base' + igram_sec + '.reg2.dat')

    # - Create Output Directory
    out_dir = make_dir(data_dir, out_dir)
    out_dir = make_dir(out_dir, igram_ref + '--' + igram_sec)

    # Change the current working directory
    os.chdir(out_dir)

    # - Resampling Secondary Interferogram on the Reference grid.
    pg.map_trans(sec_par, sec_interf, ref_par,
                 os.path.join('.', 'coco' + igram_sec
                              + '.reg2.intf.flat.topo_off.res'),
                 '-', '-', '-', 1)

    # - Path to co-registered complex interferogram
    reg_intf\
        = os.path.join('.', 'coco' + igram_sec + '.reg2.intf.flat.topo_off.res')

    # - Combine Complex Interferograms
    pg.comb_interfs(ref_interf, reg_intf, ref_base, sec_base, 1, -1,
                    dem_width,
                    'coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.geo',
                    'base' + igram_ref + '-' + igram_sec + '.flat.topo_off.geo',
                    )

    # - Show Double Difference on Top of the Reference SLC power image
    pg9.rasmph_pwr('coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.geo',
                   ref_pwr, dem_width)

    # - Smooth the obtained interferogram with pg.adf
    # - Adaptive interferogram filter using the power spectral density.
    pg.adf('coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.geo',
           'coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.geo.filt',
           'coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.geo.filt.coh',
           dem_width)
    pg9.rasmph_pwr('coco' + igram_ref + '-' + igram_sec
                   + '.flat.topo_off.geo.filt', ref_pwr, dem_width)

    # - Calculate real part, imaginary part, intensity, magnitude,
    # - or phase of FCOMPLEX data
    # - Extract Interferogram Phase.
    pg9.cpx_to_real('coco' + igram_ref + '-' + igram_sec
                    + '.flat.topo_off.geo.filt',
                    'phs.geo', dem_width, 4)
    pg9.raspwr('phs.geo', dem_width)
    # - Save Geocoded Interferogram phase as a GeoTiff
    pg9.data2geotiff(ref_par, 'phs.geo', 2,
                     'coco' + igram_ref + '-' + igram_sec
                     + '.flat.topo_off.geo.filt.tiff', -9999)
    # - Save Coherence Interferogram Map as a GeoTiff
    pg9.data2geotiff(ref_par, 'coco' + igram_ref + '-' + igram_sec
                     + '.flat.topo_off.geo.filt.coh', 2,
                     'coco' + igram_ref + '-' + igram_sec
                     + '.flat.topo_off.geo.filt.coh.tiff', -9999)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f'# - Computation Time: {end_time - start_time}')
