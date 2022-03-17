#!/bin/zsh
# - Read ICEYE SLCs provided in HDF5 format.
python read_iceye_h5.py

# - Compute Multi-looked version of the available SLCs
# - Calculate a raster image from data with power-law scaling
python multi_look_slc.py

# - Compute Preliminary Offsets for the selected pair of SLCs
python compute_offsets.py

# - Run preliminary AMPCOR analysis
python c_ampcor_iceye.py --pair=ICEYE_X7_SLC_SM_152307_20211022T145808-ICEYE_X7_SLC_SM_152566_20211023T145809