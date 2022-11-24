#!/bin/zsh

# - Read Available SLCs
python read_iceye_h5.py /u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir
python multi_look_slc.py --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output/slc+par

# - Pair 152735_20211024T145811-152987_20211025T145812
# - Decimate State Vector [Needed to run on an older version of GAMMA]
python decimate_state_vect.py --slc=152735_20211024T145811 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --replace
python decimate_state_vect.py --slc=152987_20211025T145812 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --replace


# - Compute Interferogram
python compute_offsets.py  /u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output 152735_20211024T145811 152987_20211025T145812
python c_ampcor_iceye.py --pair=152735_20211024T145811-152987_20211025T145812 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --np=40

# -> Run AMPCOR

# - Compute Interferogram
python compute_interferogram.py --pair=152735_20211024T145811-152987_20211025T145812 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output
python rm_topo_phase.py --pair=152735_20211024T145811-152987_20211025T145812 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --filter

# - Pair 154480_20211028T145816-154755_20211029T145817
# - Decimate State Vector [Needed to run on an older version of GAMMA]
python decimate_state_vect.py --slc=154480_20211028T145816 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --replace
python decimate_state_vect.py --slc=154755_20211029T145817 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --replace


# - Compute Interferogram
python compute_offsets.py 154480_20211028T145816 154755_20211029T145817 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output
python c_ampcor_iceye.py --pair=154480_20211028T145816-154755_20211029T145817 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --np=40

# -> Run AMPCOR

# - Compute Interferogram
python compute_interferogram.py --pair=154480_20211028T145816-154755_20211029T145817 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output
python rm_topo_phase.py --pair=154480_20211028T145816-154755_20211029T145817 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output --filter

# - Compute Double Difference
python ddiff_iceye.py 152735_20211024T145811-152987_20211025T145812 154480_20211028T145816-154755_20211029T145817 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output

# - Compute Double Difference using Geocoded Interferogram
python ddiff_iceye_geo.py 152735_20211024T145811-152987_20211025T145812 154480_20211028T145816-154755_20211029T145817 --directory=/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output