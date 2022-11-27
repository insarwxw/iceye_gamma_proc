#!/usr/bin/env python
u"""
Enrico Ciraci' - 06/2022

Geocode the selected input Raster.

usage: geocode_raster.py [-h] [--directory DIRECTORY] [--raster RASTER] [--par PAR]


optional arguments:
  -h, --help            show this help message and exit
  --directory DIRECTORY, -D DIRECTORY
                        Absolute path to working directory.
  --raster RASTER, -R RASTER
                        Selected raster file name.
  --par PAR, -P PAR     Selected raster parameter file.

PYTHON DEPENDENCIES:
    argparse: Parser for command-line options, arguments and sub-commands
           https://docs.python.org/3/library/argparse.html
    numpy: The fundamental package for scientific computing with Python
          https://numpy.org/
    datetime: Basic date and time types
           https://docs.python.org/3/library/datetime.html#module-datetime

    py_gamma: GAMMA's Python integration with the py_gamma module

UPDATE HISTORY:
    06/22/2022 - By default, the current directory is used as working directory.
"""
# - Python dependencies
from __future__ import print_function
import os
import sys
import argparse
import datetime
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
# - Utility functions
from utils.path_to_dem import path_to_gimp
from utils.read_keyword import read_keyword
from utils.make_dir import make_dir


def main() -> None:
    # - Read the system arguments listed after the program
    parser = argparse.ArgumentParser(
        description="""Geocode the selected input Raster."""
    )
    # - Absolute Path to selected Raster
    parser.add_argument('--directory', '-D',
                        type=str,
                        default=os.getcwd(),
                        help='Absolute path to working directory.')
    parser.add_argument('--raster', '-R',
                        type=str,
                        default=None,
                        help='Selected raster file name.')
    parser.add_argument('--par', '-P',
                        type=str,
                        default=None,
                        help='Selected raster parameter file.')

    args = parser.parse_args()

    if args.raster is None:
        print('# - Provide selected Raster names as: --path=/dir1/dir2/...')
        sys.exit()

    # - create output directory
    out_dir = make_dir(args.directory, args.raster+'.geocoded')
    # - Change the current working directory
    os.chdir(out_dir)
    # - create symbolic links to input files
    if not os.path.isfile(os.path.join('.', args.raster)):
        os.symlink(os.path.join(args.directory, args.raster),
                   os.path.join('.', args.raster))
    if not os.path.isfile(os.path.join('.', args.par)):
        os.symlink(os.path.join(args.directory, args.par),
                   os.path.join('.', args.par))
    # - Absolute path to Reference raster and to its parameter file
    ref_raster = os.path.join(out_dir, args.raster)
    par_file = os.path.join(out_dir, args.par)

    print('# - Calculate terrain-geocoding lookup table and DEM derived '
          'data products.')
    # - Calculate terrain-geocoding lookup table and DEM derived data products.
    # - pg.gc_map requires as input.
    #   MLI_par         (input) ISP MLI or SLC image parameter file
    #                           (slant range geometry)
    #   OFF_par         (input) ISP offset/interferogram parameter file
    #                           (enter - if geocoding SLC or MLI data)
    #   DEM_par         (input) DEM/MAP parameter file
    #   DEM             (input) DEM data file (or constant height value)
    #   DEM_seg_par     (input/output) DEM/MAP segment parameter file used for
    #                    output products
    #   DEM_seg         (output) DEM segment used for output products,
    #                            interpolated if lat_ovr > 1.0 or lon_ovr > 1.0
    #   lookup_table    (output) geocoding lookup table (fcomplex)
    #   lat_ovr         latitude or northing output DEM oversampling factor
    #                            (enter - for default: 1.0)
    #   lon_ovr         longitude or easting output DEM oversampling factor
    #                            (enter - for default: 1.0)
    #   sim_sar         (output) simulated SAR backscatter image in DEM geometry
    #                            (enter - for none)
    #   u               (output) zenith angle of surface normal vector n
    #                            (angle between z and n, enter - for none)
    #   v               (output) orientation angle of n (between x & projection
    #                            of n in xy plane, enter - for none)
    #   inc             (output) local incidence angle (between surface normal
    #                            and look vector, enter - for none)
    #   psi             (output) projection angle (between surface normal and
    #                            image plane normal, enter - for none)
    #   pix             (output) pixel area normalization factor
    #                           (enter - for none)
    #   ls_map          (output) layover and shadow map (in map projection,
    #                            enter - for none)
    #   frame           number of DEM pixels to add around area covered by
    #                           SAR image (enter - for default = 8)
    #   ls_mode         output lookup table values in regions of layover,
    #                           shadow, or DEM gaps (enter - for default)
    #                     0: set to (0.,0.)
    #                     1: linear interpolation across these regions
    #                           (not available in gc_map2)
    #                     2: actual value (default)
    #                     3: nn-thinned (not available in gc_map2)
    #   r_ovr           range over-sampling factor for nn-thinned
    #                          layover/shadow mode (enter - for default: 2.0)

    pg.gc_map(par_file, '-',
              os.path.join(path_to_gimp(), 'DEM_gc_par'),
              os.path.join(path_to_gimp(), 'gimpdem100.dat'),
              'DEM_gc_par', 'DEMice_gc', 'gc_icemap',
              10, 10, 'sar_map_in_dem_geometry',
              '-', '-', 'inc.geo', '-', '-', '-', '-', '2', '-'
              )

    # - Read Raster Parameter Dictionary
    ras_param_dict = pg.ParFile(par_file).par_dict
    # - read raster number of columns and rows
    raster_width = int(ras_param_dict['range_samples'][0])
    raster_lines = int(ras_param_dict['azimuth_lines'][0])
    print(f'# - Input Raster Size: {raster_lines} x {raster_width}')

    # - Extract DEM Size from parameter file
    dem_par_path = os.path.join('.', 'DEM_gc_par')
    try:
        dem_param_dict = pg.ParFile(dem_par_path).par_dict
        dem_width = int(dem_param_dict['width'][0])
        dem_nlines = int(dem_param_dict['nlines'][0])
    except IndexError:
        dem_width = int(read_keyword(dem_par_path, 'width'))
        dem_nlines = int(read_keyword(dem_par_path, 'nlines'))

    print(f'# - DEM Size: {dem_nlines} x {dem_width}')

    # - Geocode Output interferogram
    # - Geocode Double Difference
    # - Reference Interferogram look-up table
    ref_gcmap = os.path.join('.', 'gc_icemap')
    dem_par_path = os.path.join('.', 'DEM_gc_par')
    # -  Width of Geocoding par (reference)
    dem_width = int(read_keyword(dem_par_path, 'width'))
    # -  #Lines of Geocoding par (secondary)
    dem_nlines = int(read_keyword(dem_par_path, 'nlines'))
    # - geocode interferogram
    pg.geocode_back(ref_raster,
                    raster_width,
                    ref_gcmap,
                    ref_raster+'.geo',
                    dem_width, dem_nlines,
                    '-', 0
                    )

    # - Calculate a raster image from data with power-law scaling
    pg.raspwr(ref_raster+'.geo', dem_width)

    # - Save Geocoded Raster as a GeoTiff
    print('geotiff conversion')
    pg.data2geotiff(dem_par_path, ref_raster+'.geo.bmp', 0,
                    ref_raster+'.geo.tif')

    # - Change Permission Access to all the files contained inside the
    # - output directory.
    for out_file in os.listdir('.'):
        os.chmod(out_file, 0o0755)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f'# - Computation Time: {end_time - start_time}')
