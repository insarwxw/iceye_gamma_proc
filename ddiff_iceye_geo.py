"""
Enrico Ciraci' - 03/2022

Compute Double-Difference Interferogram from ICEYE data.
- Use Geocoded Interferograms.
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
        selected pair of Geocoded Interferograms.
        """
    )
    # - Positional Arguments - Reference and Secondary SLCs.
    parser.add_argument('reference', type=str, default=None,
                        help='Reference Interferogram')
    parser.add_argument('secondary', type=str, default=None,
                        help='Secondary Interferogram')

    # - Working Directory directory.
    default_dir = os.path.join(os.path.expanduser('~'), 'Desktop',
                               'iceye_gamma_test', 'output')
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

    # - Path to Geocoded Interferogram Parameter Files
    ref_par = os.path.join(data_dir_ref, 'DEM_gc_par')
    sec_par = os.path.join(data_dir_sec, 'DEM_gc_par')

    try:
        dem_param_dict = pg.ParFile(ref_par).par_dict
        dem_width = int(dem_param_dict['width'][0])
        dem_nlines = int(dem_param_dict['nlines'][0])
    except IndexError:
        dem_width = int(read_keyword(ref_par, 'width'))
        dem_nlines = int(read_keyword(ref_par, 'nlines'))

    # - Reference SLCs for the selected interferograms
    ref_pair_ref = os.path.join(data_dir_ref, igram_ref.split('-')[0])
    ref_pair_sec = os.path.join(data_dir_sec, igram_sec.split('-')[0])

    # - Geocoded Interferograms
    ref_interf = os.path.join(data_dir_ref,
                              'coco' + igram_ref + '.flat.topo_off.geo')
    ref_pwr = os.path.join(data_dir_ref, igram_ref.split('-')[0] + '.pwr1.geo')
    # -
    sec_interf = os.path.join(data_dir_sec,
                              'coco' + igram_sec + '.flat.topo_off.geo')
    sec_pwr = os.path.join(data_dir_sec, igram_sec.split('-')[0] + '.pwr1.geo')

    # - Path to Interferograms Baseline Files
    ref_base = os.path.join(data_dir_ref, 'base' + igram_ref + '.dat')
    sec_base = os.path.join(data_dir_sec, 'base' + igram_sec + '.dat')

    # - Create Output Directory
    if args.init_offset:
        out_dir = make_dir(args.directory, 'ddiff_io_geo')
    else:
        out_dir = make_dir(args.directory, 'ddiff_geo')
    out_dir = make_dir(out_dir, igram_ref + '--' + igram_sec)

    # Change the current working directory
    os.chdir(out_dir)

    # - Resampling Secondary Interferogram on the Reference grid.
    pg.map_trans(sec_par, sec_interf, ref_par,
                 os.path.join('.', 'coco' + igram_sec
                              + '.flat.topo_off.geo.res'),
                 '-', '-', '-', 1)

    # - Path to co-registered complex interferogram
    reg_intf = os.path.join('.', 'coco' + igram_sec + '.flat.topo_off.geo.res')

    # - Combine Complex Interferograms
    pg.comb_interfs(ref_interf, reg_intf, ref_base, sec_base, 1, -1,
                    dem_width,
                    'coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.geo',
                    'base' + igram_ref + '-' + igram_sec + '.flat.topo_off.geo',

                    )

    # - Read Double Difference Parameter file
    pg.rasmph_pwr('coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.geo',
                  ref_pwr, dem_width)

    # - Smooth the obtained interferogram with pg.adf
    # - Adaptive interferogram filter using the power spectral density.
    pg.adf('coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.geo',
           'coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.geo.filt',
           'coco' + igram_ref + '-' + igram_sec + '.flat.topo_off.geo.filt.coh',
           dem_width)
    pg.rasmph_pwr('coco' + igram_ref + '-' + igram_sec
                  + '.flat.topo_off.geo.filt', ref_pwr, dem_width)

    # - Calculate real part, imaginary part, intensity, magnitude,
    # - or phase of FCOMPLEX data
    # - Extract Interferogram Phase.
    pg.cpx_to_real('coco' + igram_ref + '-' + igram_sec
                   + '.flat.topo_off.geo.filt',
                   'phs.geo', dem_width, 4)
    pg.raspwr('phs.geo', dem_width)
    # - Save Geocoded Interferogram phase as a GeoTiff
    pg.data2geotiff(ref_par, 'phs.geo', 2,
                    'coco' + igram_ref + '-' + igram_sec
                    + '.flat.topo_off.geo.filt.tiff', -9999)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f'# - Computation Time: {end_time - start_time}')