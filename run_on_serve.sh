#!/bin/zsh
python read_iceye_h5.py --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir
python multi_look_slc.py --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output/slc+par
python compute_offsets.py --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output
python c_ampcor_iceye.py --pair=152307_20211022T145808-152566_20211023T145809 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --np=40