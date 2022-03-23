#!/bin/zsh

# - Read Available SLCs
python read_iceye_h5.py --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir
python multi_look_slc.py --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output/slc+par

# - Decimate State Vector [Needed to run on an older version of GAMMA]
python decimate_state_vect.py --slc=152735_20211024T145811 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --replace
python decimate_state_vect.py --slc=152987_20211025T145812 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --replace


python compute_offsets.py 152735_20211024T145811-152987_20211025T145812 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output
python c_ampcor_iceye.py --pair=152735_20211024T145811-152987_20211025T145812 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --np=40
python compute_interferogram.py --pair=152735_20211024T145811-152987_20211025T145812 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output

# - Decimate State Vector
python decimate_state_vect.py --slc=152735_20211024T145811 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --replace
python decimate_state_vect.py --slc=152987_20211025T145812 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --replace