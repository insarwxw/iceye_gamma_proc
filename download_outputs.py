# - Download ICEYE Outputs - Template
rsync -rav -e ssh --include '*/' --include='*.coh.tiff'  --exclude='*'  eciraci@mawson.ess.uci.edu:/u/mawson-r0/eric/ICEye_2021_PETERMAN/DATA_REPOSITORY/Peterman_Glacier_X7_extended_range_SLC/test.dir/output/ddiff_geo
