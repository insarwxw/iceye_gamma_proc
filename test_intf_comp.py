#!/usr/bin/env python
# - Python Dependencies
from __future__ import print_function
import os
import argparse
import datetime
import shutil
import numpy as np
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
import py_gamma2019 as pg9
# - ST_Release dependencies
from scipy.signal import medfilt
from astropy.convolution import convolve, Box2DKernel
from st_release.madian_filter_off import median_filter_off
from st_release.fill_nodata import fill_nodata
from utils.path_to_dem import path_to_dem
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
    # - Read the system arguments listed after the program
    parser = argparse.ArgumentParser(
        description="""Compute Interferogram for the selected pair.
            """
    )
    # - Primary and secondary SLCs
    parser.add_argument('reference', type=str,
                        help='Reference SLCs.')

    parser.add_argument('secondary', type=str,
                        help='Secondary SLCs.')

    parser.add_argument('dem', type=str,
                        choices=['gis', 'gimp', 'greenland',
                                 'ais', 'antarctica', 'bedmap2', 'rema'],
                        help='Digital Elevation Model used to '
                             'Remove Topographic Contribution '
                             'from Flattened Interferogram.',
                        )

    # - Working Directory directory.
    parser.add_argument('--directory', '-D',
                        type=str, default=os.getcwd(),
                        help='Project data directory.')

    parser.add_argument('--filter', '-F',
                        help='Use ADF filter to smooth interferogram phase.',
                        action='store_true')

    args = parser.parse_args()

    # - Reference and Secondary SLCs
    ref = args.reference
    sec = args.secondary

    # - Data directory
    data_dir = args.directory

    # - Resample the registered secondary SLC to the reference SLC
    # - using the using a 2-D offset map computed above.
    pg.SLC_interp_map(os.path.join(data_dir, f'{sec}.reg.slc'),
                      os.path.join(data_dir, f'{ref}.par'),
                      os.path.join(data_dir, f'{sec}.reg.par'),
                      os.path.join(data_dir, f'dense_offsets.par'),
                      os.path.join(data_dir, f'{sec}.reg2.slc'),
                      os.path.join(data_dir, f'{sec}.reg2.par'),
                      os.path.join(data_dir, f'dense_offsets.par'),
                      os.path.join(data_dir, f'dense_offsets.filt'),
                      '-', '-', 0, 7
                      )

    # - Generate a new parameter file ISP offset and interferogram
    # - parameter files.
    # - Create New ISP Parameter file
    create_isp_par(data_dir, ref, f'{sec}.reg2')

    # - Compute Interferogram
    pg.SLC_intf(os.path.join(data_dir, f'{ref}.slc'),
                os.path.join(data_dir, f'{sec}.reg2.slc'),
                os.path.join(data_dir, f'{ref}.par'),
                os.path.join(data_dir, f'{sec}.reg2.par'),
                os.path.join(data_dir, f'{ref}-{sec}.reg2.par'),
                os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf'),
                15, 15      # number of range/azimuth looks
                )
    # - Estimate baseline from orbit state vectors
    pg.base_orbit(os.path.join(data_dir, f'{ref}.par'),
                  os.path.join(data_dir, f'{sec}.reg2.par'),
                  os.path.join(data_dir, f'base{ref}-{sec}.reg2.dat'),
                  )

    # - Estimate and Remove Flat Earth Contribution from the Interferogram
    pg.ph_slope_base(os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf'),
                     os.path.join(data_dir, f'{ref}.par'),
                     os.path.join(data_dir, f'{ref}-{sec}.reg2.par'),
                     os.path.join(data_dir, f'base{ref}-{sec}.reg2.dat'),
                     os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat'),
                     )
    # - Calculate a multi-look intensity (MLI) image from the reference SLC
    pg.multi_look(os.path.join(data_dir, f'{ref}.slc'),
                  os.path.join(data_dir, f'{ref}.par'),
                  os.path.join(data_dir, f'{ref}.mli'),
                  os.path.join(data_dir, f'{ref}.mli.par'),
                  15, 15
                  )

    # - Extract interferogram dimensions from its parameter file
    igram_param_dict \
        = pg.ParFile(os.path.join(data_dir, f'{ref}-{sec}.reg2.par'),).par_dict
    # - read interferogram number of columns
    interf_width = int(igram_param_dict['interferogram_width'][0])
    interf_lines = int(igram_param_dict['interferogram_azimuth_lines'][0])
    print(f'# - Interferogram Size: {interf_lines} x {interf_width}')

    # - Adaptive interferogram filter using the power spectral density
    pg.adf(os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat'),
           os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat.filt'),
           os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat.coh'),
           interf_width
           )

    # - Generate 8-bit greyscale raster image of intensity multi-looked SLC
    pg9.raspwr(os.path.join(data_dir, f'{ref}.mli'), interf_width)

    # - Show Output Interferogram
    pg9.rasmph_pwr(
        os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat.filt'),
        os.path.join(data_dir, f'{ref}.mli.bmp'), interf_width
    )

    # - Estimate and Remove Topographic Phase from the flattened interferogram
    dem = args.dem
    dem_info = path_to_dem(dem)
    dem_info['path'] = dem_info['path']
    dem_par = os.path.join(dem_info['path'].replace(' ', '\ '), dem_info['par'])
    dem = os.path.join(dem_info['path'].replace(' ', '\ '), dem_info['dem'])
    data_dir_gc = data_dir.replace(' ', '\ ')

    pg.gc_map(os.path.join(data_dir_gc, f'{ref}.par'),
              os.path.join(data_dir_gc, f'{ref}-{sec}.reg2.par'),
              dem_par,  # - DEM/MAP parameter file
              dem,  # - DEM data file (or constant height value)
              dem_info['par'],  # - DEM segment used...
              'DEMice_gc',  # - DEM segment used for output products...
              'gc_icemap',  # - geocoding lookup table (fcomplex)
              dem_info['oversample'], dem_info['oversample'],
              'sar_map_in_dem_geometry',
              '-', '-', 'inc.geo', '-', '-', '-', '-', '2', '-'
              )

    # - Extract DEM Size from parameter file
    dem_par_path = os.path.join('.', 'DEM_gc_par')
    dem_param_dict = pg.ParFile(dem_par_path).par_dict
    dem_width = int(dem_param_dict['width'][0])
    dem_nlines = int(dem_param_dict['nlines'][0])

    print(f'# - DEM Size: {dem_nlines} x {dem_width}')

    # - Forward geocoding transformation using a lookup table
    pg.geocode('gc_icemap', 'DEMice_gc', dem_width, 'hgt_icemap',
               interf_width, interf_lines)
    pg.geocode('gc_icemap', 'inc.geo', dem_width, 'inc',
               interf_width, interf_lines)

    # - Invert geocoding lookup table
    pg.gc_map_inversion('gc_icemap', dem_width, 'gc_map_invert',
                        interf_width, interf_lines)

    # - Geocoding of Reference SLC power using a geocoding lookup table
    pg.geocode_back(os.path.join(data_dir, f'{ref}.mli'), interf_width,
                    'gc_icemap',
                    os.path.join(data_dir, f'{ref}.mli.geo'),
                    dem_width, dem_nlines)
    pg9.raspwr(os.path.join(data_dir, f'{ref}.mli.geo'), dem_width)

    # - Remove Interferometric Phase component due to surface Topography.
    # - Simulate unwrapped interferometric phase using DEM height.
    pg.phase_sim(os.path.join(data_dir, f'{ref}.par'),
                 os.path.join(data_dir, f'{ref}-{sec}.reg2.par'),
                 os.path.join(data_dir, f'base{ref}-{sec}.reg2.dat'),
                 'hgt_icemap',
                 'sim_phase', 1, 0, '-'
                 )
    # - Create DIFF/GEO parameter file for geocoding and
    # - differential interferometry
    pg.create_diff_par(os.path.join(data_dir, f'{ref}-{sec}.reg2.par'),
                       os.path.join(data_dir, f'{ref}-{sec}.reg2.par'),
                       'DIFF_par', '-', 0)

    # - Subtract topographic phase from interferogram
    pg.sub_phase(os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat'),
                 'sim_phase', 'DIFF_par',
                 os.path.join(data_dir,
                              f'coco{ref}-{sec}.reg2.intf.flat.topo_off'), 1
                 )
    # - Show interferogram w/o topographic phase
    pg9.rasmph_pwr(os.path.join(data_dir,
                                f'coco{ref}-{sec}.reg2.intf.flat.topo_off'),
                   os.path.join(data_dir, f'{ref}.mli'), interf_width)

    # - Geocode Output interferogram
    # - Reference Interferogram look-up table
    ref_gcmap = os.path.join('.', 'gc_icemap')

    # - geocode interferogram
    pg.geocode_back(
        os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat.topo_off'),
        interf_width,  ref_gcmap,
        os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat.topo_off.geo'),
        dem_width, dem_nlines, '-', 1
    )

    # - Show Geocoded interferogram
    pg9.rasmph_pwr(
        os.path.join(data_dir, f'coco{ref}-{sec}.reg2.intf.flat.topo_off.geo'),
        os.path.join(data_dir, f'{ref}.mli.geo'),  dem_width
    )

    if args.filter:
        # - Smooth the obtained interferogram with pg.adf
        # - Adaptive interferogram filter using the power spectral density.
        pg.adf(os.path.join(data_dir,
                            f'coco{ref}-{sec}.reg2.intf.flat.topo_off'),
               os.path.join(data_dir,
                            f'coco{ref}-{sec}.reg2.intf.flat.topo_off.filt'),
               os.path.join(data_dir,
                            f'coco{ref}-{sec}.reg2.intf.flat.'
                            f'topo_off.filt.coh'),
               dem_width)
        # - Show filtered interferogram
        pg9.rasmph_pwr(
            os.path.join(data_dir,
                         f'coco{ref}-{sec}.reg2.intf.flat.topo_off.filt'),
            os.path.join(data_dir, f'{ref}.mli'), interf_width
        )

        # - Smooth Geocoded Interferogram
        pg.adf(os.path.join(data_dir,
                            f'coco{ref}-{sec}.reg2.intf.flat.topo_off.geo'),
               os.path.join(data_dir,
                            f'coco{ref}-{sec}.reg2.intf.flat.'
                            f'topo_off.geo.filt'),
               os.path.join(data_dir,
                            f'coco{ref}-{sec}.reg2.intf.flat.topo_off.geo.'
                            f'filt.coh'),
               dem_width)
        # - Show filtered interferogram
        pg9.rasmph_pwr(
            os.path.join(data_dir,
                         f'coco{ref}-{sec}.reg2.intf.flat.topo_off.geo.filt'),
            os.path.join(data_dir, f'{ref}.mli.geo'), dem_width
        )

    # - Change Permission Access to all the files contained inside the
    # - output directory.
    for out_file in os.listdir('.'):
        os.chmod(out_file, 0o0755)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")
