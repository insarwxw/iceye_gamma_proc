#!/usr/bin/env python
# - Python Dependencies
from __future__ import print_function
import os
import argparse
import datetime
import shutil
import subprocess
from multiprocessing import Pool
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
import py_gamma2019 as pg9
# - Package Dependencies
from c_ampcor_iceye import c_ampcor_iceye
from interp_sec_slc import register_slc
# - ST_Release dependencies
from st_release.r_off_sar import r_off_sar
from st_release.c_off4intf import c_off4intf
from utils.make_dir import make_dir
from utils.path_to_dem import path_to_dem


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
        os.path.join(data_dir, f'{ref_slc}.par'),
        os.path.join(data_dir, f'{sec_slc}.par'),
        os.path.join(data_dir, f'{ref_slc}-{sec_slc}.par'),
        algorithm, rlks, azlks, iflg
    )
    # - Initial SLC image offset estimation from orbit state-vectors
    # - and image parameters
    pg.init_offset_orbit(
        os.path.join(data_dir, f'{ref_slc}.par'),
        os.path.join(data_dir, f'{sec_slc}.par'),
        os.path.join(data_dir, f'{ref_slc}-{sec_slc}.par')
    )


def run_sub_process(cmd: list[str]) -> None:
    """
    Run a command in a subprocess
    :param cmd: command to run
    :return: None
    """
    # - Run the command
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(cmd,
                              stdout=devnull,
                              stderr=subprocess.STDOUT)


def main() -> None:
    # - Read the system arguments listed after the program
    parser = argparse.ArgumentParser(
        description="""Run Interferometric Processing (ISP) on a pair of SLCs."""
    )
    # - Reference SLCs
    parser.add_argument('ref_slc', type=str,
                        help='Reference SLCs.')
    # - Secondary SLCs
    parser.add_argument('sec_slc', type=str,
                        help='Secondary SLCs.')
    # - Digital Elevation Model (DEM)
    parser.add_argument('dem', type=str,
                        choices=['gis', 'gimp', 'greenland',
                                 'ais', 'antarctica', 'bedmap2', 'rema'],
                        help='Digital Elevation Model used to '
                             'Remove Topographic Contribution '
                             'from Flattened Interferogram.',
                        )
    # - Data Directory
    parser.add_argument('--directory', '-D',
                        help='Data directory.',
                        default=os.getcwd())
    # - Output Directory
    parser.add_argument('--out_directory', '-O', help='Output directory.',
                        default=os.getcwd())

    # - Number of Parallel Processes
    parser.add_argument('--n_proc', '-N',
                        type=int, default=15,
                        help='Number of Parallel Processes.')

    # - AMPCOR Binary Selected
    parser.add_argument('--ampcor', '-A',
                        type=str, default='ampcor_large',
                        choices=['ampcor_large', 'ampcor_large2',
                                 'ampcor_superlarge2'],
                        help='AMPCOR Binary Selected.')

    # - Register SLCs using 3rd order polynomial
    # - Obtained by computing preliminary dense offsets field
    parser.add_argument('--pdoff', '-p',
                        help='Compute preliminary dense offsets field.',
                        action='store_true')

    # - Number of Looks in Range
    parser.add_argument('--nrlks', type=int, default=None,
                        help='Number of looks Range.')
    # - Number of Looks in Azimuth
    parser.add_argument('--nazlks', type=int, default=None,
                        help='Number of looks Azimuth.')
    args = parser.parse_args()

    # - Read input parameters
    ref_slc = args.ref_slc      # - Reference SLC
    sec_slc = args.sec_slc      # - Secondary SLC
    data_dir = args.directory   # - Data directory
    out_dir = args.out_directory    # - Output directory
    n_proc = args.n_proc        # - Number of parallel processes
    ampcor_bin = args.ampcor    # - AMPCOR binary selected
    pdoff = args.pdoff          # - Compute preliminary dense offsets field
    dem = args.dem              # - DEM file for Geocoding and Topo Phase Removal

    # # - Compute ISP Parameters
    # create_isp_par(data_dir, ref_slc, sec_slc)
    #
    # # - Register SLC-2 to SLC-1 using 3rd order polynomial
    # register_slc(ref_slc, sec_slc,  # - Reference and Secondary SLC
    #              pdoff=pdoff,       # - Compute preliminary dense offsets field
    #              data_dir=data_dir,     # - Path to data directory
    #              out_dir=out_dir)       # - Path to output directory
    #
    # # - Create the bat file to run AMPCOR
    sec_slc = f'{sec_slc}.reg'  # - Secondary SLC registered to reference SLC
    # c_ampcor_iceye(ref_slc, sec_slc,    # - Reference and Secondary SLC
    #                data_dir=data_dir,   # - Path to data directory
    #                out_dir=out_dir,     # - Path to output directory
    #                n_proc=n_proc,       # - Number of parallel processes
    #                ampcor=ampcor_bin)   # - AMPCOR binary selected
    #
    # print('# - Run AMPCOR.')
    # # - Read ampcor bat file
    # with open(os.path.join(out_dir, f'bat_{ref_slc}-{sec_slc}')) as r_fid:
    #     sub_proc = r_fid.readlines()
    # sub_proc_list = [s.split(' ')[0:2] for s in sub_proc]
    #
    # # - Run AMPCOR
    # with Pool(n_proc) as p:
    #     p.map(run_sub_process, sub_proc_list)
    #
    # print('# - AMPCOR Run Completed.')

    # - Process offsets - Stack offset files
    r_off_sar(data_dir, ref_slc, sec_slc)

    # - Process offsets for Interferogram
    c_off4intf(data_dir, ref_slc, sec_slc,
               range_spacing=30, azimuth_spacing=30,
               filter_strategy=2, smooth=True,
               fill=False, nrlks=args.nrlks, nazlks=args.nazlks)

    # - Make Save directory
    save_dir = make_dir(data_dir, 'Save')
    # # - Move offsets calculated by AMPCOR into OFFSETS
    # off_file_list = [os.path.join('.', x) for x in os.listdir('.')
    #                  if '.offmap_' in x]
    # for f_mv in off_file_list:
    #     shutil.move(f_mv, save_dir)

    # - Resample the registered secondary SLC to the reference SLC
    # - using the using a 2-D offset map computed above.
    offset_par = f'{ref_slc}-{sec_slc}.offmap.par.interp'
    offset_interp = f'{ref_slc}-{sec_slc}.offmap.off.new.interp'
    pg.SLC_interp_map(
        os.path.join(data_dir, f'{sec_slc}.slc'),  # - Secondary SLC
        os.path.join(data_dir, f'{ref_slc}.par'),      # - Reference SLC par file
        os.path.join(data_dir, f'{sec_slc}.par'),  # - Secondary SLC par file
        os.path.join(data_dir, offset_par),            # - Offsets par file
        os.path.join(data_dir, f'{sec_slc}.reg2.slc'),  # - Output SLC
        os.path.join(data_dir, f'{sec_slc}.reg2.par'),  # - Output SLC par file
        os.path.join(data_dir, offset_par),            # - Offsets par file
        os.path.join(data_dir, offset_interp),         # - Offsets file
        '-', '-', 0, 7
    )

    # - Generate a new parameter file ISP offset and interferogram
    # - parameter files.
    # - Create New ISP Parameter file
    create_isp_par(data_dir, ref_slc, f'{sec_slc}.reg2')

    # - Compute Interferogram
    pg.SLC_intf(os.path.join(data_dir, f'{ref_slc}.slc'),
                os.path.join(data_dir, f'{sec_slc}.reg2.slc'),
                os.path.join(data_dir, f'{ref_slc}.par'),
                os.path.join(data_dir, f'{sec_slc}.reg2.par'),
                os.path.join(data_dir, f'{ref_slc}-{sec_slc}.reg2.par'),
                os.path.join(data_dir, f'coco{ref_slc}-{sec_slc}.reg2.intf'),
                15, 15      # number of range/azimuth looks
                )
    # - Estimate baseline from orbit state vectors
    pg.base_orbit(os.path.join(data_dir, f'{ref_slc}.par'),
                  os.path.join(data_dir, f'{sec_slc}.reg2.par'),
                  os.path.join(data_dir, f'base{ref_slc}-{sec_slc}.reg2.dat'),
                  )

    # - Estimate and Remove Flat Earth Contribution from the Interferogram
    pg.ph_slope_base(
        os.path.join(data_dir, f'coco{ref_slc}-{sec_slc}.reg2.intf'),
        os.path.join(data_dir, f'{ref_slc}.par'),
        os.path.join(data_dir, f'{ref_slc}-{sec_slc}.reg2.par'),
        os.path.join(data_dir, f'base{ref_slc}-{sec_slc}.reg2.dat'),
        os.path.join(data_dir, f'coco{ref_slc}-{sec_slc}.reg2.intf.flat')
    )
    # - Calculate a multi-look intensity (MLI) image from the reference SLC
    pg.multi_look(os.path.join(data_dir, f'{ref_slc}.slc'),
                  os.path.join(data_dir, f'{ref_slc}.par'),
                  os.path.join(data_dir, f'{ref_slc}.mli'),
                  os.path.join(data_dir, f'{ref_slc}.mli.par'),
                  15, 15
                  )

    # - Extract interferogram dimensions from its parameter file
    igram_param_dict \
        = pg.ParFile(os.path.join(data_dir,
                                  f'{ref_slc}-{sec_slc}.reg2.par'),).par_dict
    # - read interferogram number of columns
    interf_width = int(igram_param_dict['interferogram_width'][0])
    interf_lines = int(igram_param_dict['interferogram_azimuth_lines'][0])
    print(f'# - Interferogram Size: {interf_lines} x {interf_width}')

    # - Adaptive interferogram filter using the power spectral density
    pg.adf(
        os.path.join(data_dir, f'coco{ref_slc}-{sec_slc}.reg2.intf.flat'),
        os.path.join(data_dir, f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.filt'),
        os.path.join(data_dir, f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.coh'),
        interf_width
    )

    # - Generate 8-bit greyscale raster image of intensity multi-looked SLC
    pg9.raspwr(os.path.join(data_dir, f'{ref_slc}.mli'), interf_width)

    # - Show Output Interferogram
    pg9.rasmph_pwr(
        os.path.join(data_dir, f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.filt'),
        os.path.join(data_dir, f'{ref_slc}.mli.bmp'), interf_width
    )

    # - Estimate and Remove Topographic Phase from the flattened interferogram
    dem_info = path_to_dem(dem)
    dem_info['path'] = dem_info['path']
    dem_par = os.path.join(dem_info['path'].replace(' ', '\ '), dem_info['par'])
    dem = os.path.join(dem_info['path'].replace(' ', '\ '), dem_info['dem'])
    data_dir_gc = data_dir.replace(' ', '\ ')

    pg.gc_map(
        os.path.join(data_dir_gc, f'{ref_slc}.par'),
        os.path.join(data_dir_gc, f'{ref_slc}-{sec_slc}.reg2.par'),
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
    pg.geocode_back(os.path.join(data_dir, f'{ref_slc}.mli'), interf_width,
                    'gc_icemap',
                    os.path.join(data_dir, f'{ref_slc}.mli.geo'),
                    dem_width, dem_nlines)
    pg9.raspwr(os.path.join(data_dir, f'{ref_slc}.mli.geo'), dem_width)

    # - Remove Interferometric Phase component due to surface Topography.
    # - Simulate unwrapped interferometric phase using DEM height.
    pg.phase_sim(os.path.join(data_dir, f'{ref_slc}.par'),
                 os.path.join(data_dir, f'{ref_slc}-{sec_slc}.reg2.par'),
                 os.path.join(data_dir, f'base{ref_slc}-{sec_slc}.reg2.dat'),
                 'hgt_icemap',
                 'sim_phase', 1, 0, '-'
                 )
    # - Create DIFF/GEO parameter file for geocoding and
    # - differential interferometry
    pg.create_diff_par(os.path.join(data_dir, f'{ref_slc}-{sec_slc}.reg2.par'),
                       os.path.join(data_dir, f'{ref_slc}-{sec_slc}.reg2.par'),
                       'DIFF_par', '-', 0)

    # - Subtract topographic phase from interferogram
    pg.sub_phase(os.path.join(data_dir, f'coco{ref_slc}-{sec_slc}.reg2.intf.flat'),
                 'sim_phase', 'DIFF_par',
                 os.path.join(data_dir,
                              f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.topo_off'), 1
                 )
    # - Show interferogram w/o topographic phase
    pg9.rasmph_pwr(os.path.join(data_dir,
                                f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.topo_off'),
                   os.path.join(data_dir, f'{ref_slc}.mli'), interf_width)

    # - Geocode Output interferogram
    # - Reference Interferogram look-up table
    ref_gcmap = os.path.join('.', 'gc_icemap')

    # - geocode interferogram
    pg.geocode_back(
        os.path.join(data_dir, f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.topo_off'),
        interf_width,  ref_gcmap,
        os.path.join(data_dir, f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.topo_off.geo'),
        dem_width, dem_nlines, '-', 1
    )

    # - Show Geocoded interferogram
    pg9.rasmph_pwr(
        os.path.join(data_dir, f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.topo_off.geo'),
        os.path.join(data_dir, f'{ref_slc}.mli.geo'),  dem_width
    )

    if args.filter:
        # - Smooth the obtained interferogram with pg.adf
        # - Adaptive interferogram filter using the power spectral density.
        pg.adf(os.path.join(data_dir,
                            f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.topo_off'),
               os.path.join(data_dir,
                            f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.topo_off.filt'),
               os.path.join(data_dir,
                            f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.'
                            f'topo_off.filt.coh'),
               dem_width)
        # - Show filtered interferogram
        pg9.rasmph_pwr(
            os.path.join(data_dir,
                         f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.topo_off.filt'),
            os.path.join(data_dir, f'{ref_slc}.mli'), interf_width
        )

        # - Smooth Geocoded Interferogram
        pg.adf(os.path.join(data_dir,
                            f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.topo_off.geo'),
               os.path.join(data_dir,
                            f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.'
                            f'topo_off.geo.filt'),
               os.path.join(data_dir,
                            f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.topo_off.geo.'
                            f'filt.coh'),
               dem_width)
        # - Show filtered interferogram
        pg9.rasmph_pwr(
            os.path.join(data_dir,
                         f'coco{ref_slc}-{sec_slc}.reg2.intf.flat.topo_off.geo.filt'),
            os.path.join(data_dir, f'{ref_slc}.mli.geo'), dem_width
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
