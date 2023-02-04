#!/bin/zsh
#  args: $1: data directory
# - Extract slc and par file
read_iceye_h5.py . --slc=$1  # from the data directory
# - multi-look slc
multi_look_slc.py xxx.slc
# - Decimate Orbit State Vector
decimate_state_vect.py xxx --replace
# - Compute Offsets
mkdir ../pair_diff
compute_offsets.py ref sec  --out_directory="../pair_diff"


