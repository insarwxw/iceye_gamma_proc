#!/usr/bin/env python
"""
Enrico Ciraci' - 03/2022

Remove Topographic Contribution from Flattened Interferogram.
"""
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
        description="""Geocode Flattened Interferogram and Remove
        Topographic Contribution to Interferometric Phase. """
    )
    # - Working Directory directory.
    default_dir = os.path.join(os.path.expanduser('~'), 'Desktop',
                               'iceye_gamma_test', 'output')

    parser.add_argument('--directory', '-D',
                        type=lambda p: os.path.abspath(
                            os.path.expanduser(p)),
                        default=default_dir,
                        help='Project data directory.')

    parser.add_argument('--pair', '-P',
                        type=str,
                        default=None,
                        help='SLC Pair Codes separated by "_" '
                             'reference-secondary')

    parser.add_argument('--filter', '-F', action='store_true',
                        help='Adaptive interferogram filter using the power '
                             'spectral density - (GAMMA - adf)')

    parser.add_argument('--init_offset', '-I', action='store_true',
                        help='Determine initial offset between SLC'
                             'images using correlation of image intensity')

    args = parser.parse_args()

    if args.pair is None:
        print('# - Provide selected SLC names as: --pair=Ref_Code_Sec_Code')
        sys.exit()

    # - Reference and Secondary SLCs
    slc_list = args.pair.split('-')
    ref_slc = slc_list[0]
    sec_slc = slc_list[1]

    # - Data directory
    if args.init_offset:
        data_dir = os.path.join(args.directory,
                                'pair_diff_io', ref_slc + '-' + sec_slc)
    else:
        data_dir = os.path.join(args.directory,
                                'pair_diff', ref_slc + '-' + sec_slc)
    # - Change the current working directory
    os.chdir(data_dir)

    # - Extract Interferogram Size from parameter file
    igram_par_path = os.path.join('.',
                                  f'{ref_slc}-{sec_slc}.offmap.par.interp')

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

    pg.gc_map(ref_slc+'.par',
              igram_par_path,
              os.path.join(path_to_gimp(), 'DEM_gc_par'),
              os.path.join(path_to_gimp(), 'gimpdem100.dat'),
              'DEM_gc_par', 'DEMice_gc', 'gc_icemap',
              10, 10, 'sar_map_in_dem_geometry',
              '-', '-', 'inc.geo', '-', '-', '-', '-', '2', '-'
              )

    igram_param_dict = pg.ParFile(igram_par_path).par_dict

    # - read interferogram number of columns
    interf_width = int(igram_param_dict['interferogram_width'][0])
    interf_lines = int(igram_param_dict['interferogram_azimuth_lines'][0])
    print(f'# - Interferogram Size: {interf_lines} x {interf_width}')

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

    # - Forward geocoding transformation using a lookup table
    pg.geocode('gc_icemap', 'DEMice_gc', dem_width, 'hgt_icemap',
               interf_width, interf_lines)
    pg.geocode('gc_icemap', 'inc.geo', dem_width, 'inc',
               interf_width, interf_lines)

    # - Create DIFF/GEO parameter file for geocoding and differential
    # - interferometry.
    pg.create_diff_par(igram_par_path, igram_par_path, 'DIFF_par', '-', 0)

    # - Invert geocoding lookup table
    pg.gc_map_inversion('gc_icemap', dem_width, 'gc_map_invert',
                        interf_width, interf_lines)

    # - Geocoding of Reference SLC power using a geocoding lookup table
    pg.geocode_back(ref_slc + '.pwr1', interf_width, 'gc_icemap',
                    ref_slc + '.pwr1.geo', dem_width, dem_nlines)
    pg.raspwr(ref_slc + '.pwr1.geo', dem_width)

    # - Remove Interferometric Phase component due to surface Topography.
    # - Simulate unwrapped interferometric phase using DEM height.
    pg.phase_sim(ref_slc + '.par', igram_par_path,
                 f'base{ref_slc}-{sec_slc}.dat', 'hgt_icemap',
                 'sim_phase', 1, 0, '-')
    # - Create DIFF/GEO parameter file for geocoding and
    # - differential interferometry
    pg.create_diff_par(igram_par_path, igram_par_path, 'DIFF_par', '-', 0)

    # - Subtract topographic phase from interferogram
    pg.sub_phase(f'coco{ref_slc}-{sec_slc}.flat', 'sim_phase', 'DIFF_par',
                 f'coco{ref_slc}-{sec_slc}.flat.topo_off', 1)
    # - Show interferogram w/o topographic phase
    pg.rasmph_pwr(f'coco{ref_slc}-{sec_slc}.flat.topo_off',
                  f'{ref_slc}.pwr1', interf_width)

    # - Geocode Output interferogram
    # - Geocode Double Difference
    # - Reference Interferogram look-up table
    ref_gcmap = os.path.join('.', 'gc_icemap')
    dem_par_path = os.path.join('.', 'DEM_gc_par')
    # -  Width of Geocoding par (reference)
    dem_width = int(read_keyword(dem_par_path, 'width'))
    # -  nlines of Geocoding par (secondary)
    dem_nlines = int(read_keyword(dem_par_path, 'nlines'))
    # - geocode interferogram
    pg.geocode_back(f'coco{ref_slc}-{sec_slc}.flat.topo_off',
                    interf_width,
                    ref_gcmap,
                    f'coco{ref_slc}-{sec_slc}.flat.topo_off.geo',
                    dem_width, dem_nlines,
                    '-', 1
                    )

    # - Show Geocoded interferogram
    pg.rasmph_pwr(f'coco{ref_slc}-{sec_slc}.flat.topo_off.geo',
                  f'{ref_slc}.pwr1.geo', dem_width)

    if args.filter:
        # - Smooth the obtained interferogram with pg.adf
        # - Adaptive interferogram filter using the power spectral density.
        pg.adf(f'coco{ref_slc}-{sec_slc}.flat.topo_off',
               f'coco{ref_slc}-{sec_slc}.flat.topo_off.filt',
               f'coco{ref_slc}-{sec_slc}.flat.topo_off.filt.coh',
               dem_width)
        # - Show filtered interferogram
        pg.rasmph_pwr(f'coco{ref_slc}-{sec_slc}.flat.topo_off.filt',
                      f'{ref_slc}.pwr1.geo', dem_width)

        # - Smooth Geocoded Interferogram
        pg.adf(f'coco{ref_slc}-{sec_slc}.flat.topo_off.geo',
               f'coco{ref_slc}-{sec_slc}.flat.topo_off.geo.filt',
               f'coco{ref_slc}-{sec_slc}.flat.topo_off.geo.filt.coh',
               dem_width)
        # - Show filtered interferogram
        pg.rasmph_pwr(f'coco{ref_slc}-{sec_slc}.flat.topo_off.geo.filt',
                      f'{ref_slc}.pwr1.geo', dem_width)

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
