"""
Enrico Ciraci' - 03/2022

Compare Double Difference Interferograms
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
    # - data directory
    data_dir = '/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output'
    # -
    dir_1 = os.path.join(data_dir, 'ddiff_geo')
    dir_2 = os.path.join(data_dir, 'ddiff_io_geo')
    intf_dir_1 = os.path.join(data_dir, 'pair_diff')
    # - output directory
    out_dir = make_dir(data_dir, 'ddiff_comp')

    # - list directory
    dir_1_listr = [os.path.join(dir_1, dr)
                   for dr in os.listdir(dir_1) if os.path.isdir(os.path.join(dir_1, dr))]
    print(dir_1_listr)

    for ddiff in dir_1_listr[:2]:
        # - extract interferograms info
        ddiff_name = ddiff.split('/')[-1]
        ref_igram = ddiff_name.split('--')[0]
        sec_igram = ddiff_name.split('--')[1]
        ref_slc = ref_igram.split('-')[0]
        print('# - Geocoded Double Difference: ' + 'coco'+ddiff_name+'.flat.topo_off.geo')
        print('# - Reference Interferogram: ' + ref_igram)
        print('# - Secondary Interferogram: ' + sec_igram)
        print('# - Reference SLC: ' + sec_igram)

        ddiff_1 = os.path.join(dir_1, ddiff_name, 'coco'+ddiff_name + '.flat.topo_off.geo')
        ddiff_2 = os.path.join(dir_2, ddiff_name, 'coco'+ddiff_name + '.flat.topo_off.geo')
        base_1 = os.path.join(dir_1, ddiff_name, 'base'+ddiff_name + '.flat.topo_off.geo')
        base_2 = os.path.join(dir_2, ddiff_name, 'base' + ddiff_name + '.flat.topo_off.geo')

        # - Path to Geocoded Interferogram Parameter Files
        data_dir_ref = os.path.join(intf_dir_1, ref_igram)
        ref_par = os.path.join(data_dir_ref, 'DEM_gc_par')

        try:
            dem_param_dict = pg.ParFile(ref_par).par_dict
            dem_width = int(dem_param_dict['width'][0])
            dem_nlines = int(dem_param_dict['nlines'][0])
        except IndexError:
            dem_width = int(read_keyword(ref_par, 'width'))
            dem_nlines = int(read_keyword(ref_par, 'nlines'))

        # - Compute Double Difference Difference
        out_diff = os.path.join(out_dir, 'coco'+ddiff_name + '.flat.topo_off.geo')
        out_base = os.path.join(out_dir, 'base'+ddiff_name + '.flat.topo_off.geo')
        pg.comb_interfs(ddiff_1, ddiff_2, base_1, base_2, 1, -1, dem_width,
                        out_diff, out_base)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f'# - Computation Time: {end_time - start_time}')
