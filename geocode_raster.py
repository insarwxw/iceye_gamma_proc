# - Python dependencies
from __future__ import print_function
import os
import sys
import argparse
import datetime
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
from utils.path_to_dem import path_to_gimp
from utils.read_keyword import read_keyword


def main() -> None:
    # - Read the system arguments listed after the program
    parser = argparse.ArgumentParser(
        description="""Geocode the selected input Raster."""
    )
    # - Absolute Path to selected Raster
    parser.add_argument('--raster', '-R',
                        type=str,
                        default=None,
                        help='Selected raster file name.')
    parser.add_argument('--par', '-P',
                        type=str,
                        default=None,
                        help='Selected raster paramter file.')

    args = parser.parse_args()

    if args.raster is None:
        print('# - Provide selected Raster names as: --path=/dir1/dir2/...')
        sys.exit()

    ref_ratser = args.raster
    par_file = args.par

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


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f'# - Computation Time: {end_time - start_time}')
