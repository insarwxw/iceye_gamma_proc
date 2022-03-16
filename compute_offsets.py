"""
Calculate Preliminary Offsets Parameter File for a pair of ICEye Single Look
Complex images using  GAMMA's Python integration with the py_gamma module.
"""
# - Python Dependencies
from __future__ import print_function
import os
import datetime
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
from utils.make_dir import make_dir


def main():
    # - Parameters
    ref = 'ICEYE_X7_SLC_SM_152307_20211022T145808'
    sec = 'ICEYE_X7_SLC_SM_152566_20211023T145809'
    # - Offset Computation parameter
    algorithm = 1       # - offset estimation algorithm
    rlks = 1   # - number of interferogram range looks (enter -  for default: 1)
    azlks = 1  # - number of interferogram azimuth looks (enter - for default: 1)
    iflg = 0   # -  interactive mode flag (enter -  for default)

    # - init_offsat - Parameters
    # - center of patch (enter - for default: image center)
    rpos = '-'   # - center of patch in range (samples)
    azpos = '-'  # - center of patch in azimuth (lines)
    offr = '-'  # - initial range offset (samples) (enter - for default: 0)
    offaz = '-'  # - initial azimuth offset (lines) (enter - for default: 0)
    thres = '-'  # - cross-correlation threshold (enter - for default: 0.150)
    rwin = 512   # - range window size (default: 512)
    azwin = 512  # - azimuth window size (default: 512)

    # - Output directory name
    out_dir_name = ref.split('_')[-1] + '_' + sec.split('_')[-1]
    # - Path to Test directory
    data_dir = os.path.join(os.path.expanduser('~'), 'Desktop',
                            'iceye_gamma_test', 'output', 'slc+par')
    # - Output Directory
    out_dir = make_dir(os.path.join(os.path.expanduser('~'), 'Desktop',
                                    'iceye_gamma_test', 'output'),
                       'pair_diff')
    out_dir = make_dir(out_dir, out_dir_name)
    # - output parameter file
    out_par = os.path.join(out_dir, out_dir_name+'.par')

    # - Create Offset Parameter File
    pg.create_offset(os.path.join(data_dir, ref+'.par'),
                     os.path.join(data_dir, sec+'.par'), out_par,
                     algorithm, rlks, azlks, iflg)

    # - Initial SLC image offset estimation from orbit state-vectors
    # - and image parameters
    pg.init_offset_orbit(os.path.join(data_dir, ref+'.par'),
                         os.path.join(data_dir, sec+'.par'), out_par)

    # - Determine initial offset between SLC images using correlation
    # - of image intensity
    pg.init_offset(os.path.join(data_dir, ref+'.slc'),
                   os.path.join(data_dir, sec+'.slc'),
                   os.path.join(data_dir, ref+'.par'),
                   os.path.join(data_dir, sec+'.par'),
                   out_par,  rlks, azlks, rpos, azpos, offr, offaz,
                   thres, rwin, azwin)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f"# - Computation Time: {end_time - start_time}")