pro process_offsets,reference_slc,secondary_slc,data_dir
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Written by Enrico Ciraci - 09/2021
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Simplified IDL script to display offsets map using outputs from AMPCOR.
;
; Input Parameters:
; reference_slc - Reference SLC
; secondary_slc - Secondary SLC
; absolute path to Project Data Directory.
;
; Dependencies:
; - ST_RELEASE/COMMON/IDL/r_off.pro - Read offsets Calculated by AMPCOR;
; - ST_RELEASE/COMMON/IDL/c_off4intf.pro - Display/Interpolate offsets
;                     Calculated by using AMPCOR;
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; To run this script:
; - enter IDL console and compile the script: .RUN process_offsets
; - from IDL console:
; - process_offsets,'20141220','20141224','path_to_dir'
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; change directory
CD, data_dir

; Read Offsets
r_off, reference_slc,secondary_slc, resp = 'y'

; Create Output Directory
FILE_MKDIR,'Save'

; Display Offsets
; c_off4intf, reference_slc, secondary_slc, rs=30, zs=30, /fill
c_off4intf, reference_slc, secondary_slc, rs=30, zs=30
end