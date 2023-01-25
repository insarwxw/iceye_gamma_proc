
import os
import numpy as np
from scipy.signal import medfilt
import matplotlib.pyplot as plt
from astropy.convolution import convolve, Box2DKernel
# -
from st_release.fill_nodata import fill_nodata
from st_release.fparam import off_param
from st_release.madian_filter_off import median_filter_off
from st_release.congrid2d import congrid2d

# - Run parameters
filter_strategy = 2
smooth = True
fill = True

# - Read Offsets Map Parameters and extract
range_spacing = 30
azimuth_spacing = 30
data_dir = os.path.join(os.path.expanduser('~'), 'Desktop', 'test_fill_no_data')
id1 = '152307_20211022T145808'
id2 = '152566_20211023T145809'

# - azimuth and range pixel spacing.
poff = off_param()
poff.load(os.path.join(data_dir, id1 + '-' + id2 + '.offmap.par'))

if range_spacing is None:
    range_spacing = int(150. / poff.rgsp)

if azimuth_spacing is None:
    azimuth_spacing = int(150. / poff.azsp)

print('# - Testing Outlier Filling Strategy:')
print('# - Range spacing :', range_spacing)
print('# - Azimuth spacing :', azimuth_spacing)

# - Read Offsets Map
offset_map_path = os.path.join(data_dir, id1 + '-' + id2 + '.offmap.off')
off_map = np.fromfile(offset_map_path, dtype=np.complex64)\
    .reshape(poff.nrec, poff.npix).byteswap()

# - Generate Ramp - Linear Ramp in the azimuth/range domain
x = np.ones([poff.nrec, 1], dtype='float32') \
    * (np.arange(poff.npix, dtype='float32').reshape([1, poff.npix]))
y = np.ones([1, poff.npix], dtype='float32') \
    * np.arange(poff.nrec, dtype='float32').reshape([poff.nrec, 1])

# - Generate Range and Azimuth axes
# - Note multiplication for pixel spacing.
x_var = poff.x_start + x * poff.rgsp
y_var = poff.y_start + y * poff.azsp

# - Generate Polynomial Ramp
ramp_offx = poff.xoff[0] + x_var * poff.xoff[1] + y_var * poff.xoff[2]
ramp_offy = poff.yoff[0] + x_var * poff.yoff[1] + y_var * poff.yoff[2]

# - Remove Erroneous Offsets s by apply Median Filter.
if filter_strategy == 1:
    # - Filtering strategy 1 - see c_off4intf.py
    med_filt_size = 9            # - Median filter Kernel Size
    med_thresh = 1               # - Median filter Threshold
elif filter_strategy == 2:
    # - Filtering Strategy 2 - see c_off3intf.pro
    med_filt_size = 15           # - Median filter Kernel Size
    med_thresh = 0.5             # - Median filter Threshold
else:
    raise ValueError('# - Unknown filtering strategy selected.')

mask = median_filter_off(off_map, size=med_filt_size, thre=med_thresh)

# - Set Outliers Mask borders equal to 1
mask[:, 0:2] = 1
mask[:, poff.npix - 2:] = 1
mask[0:2, :] = 1
mask[poff.nrec - 2:, :] = 1
# - Apply Outliers Mask to Offsets Map
# xoff_masked = np.ma.array(off_map.real, mask=mask)
# yoff_masked = np.ma.array(off_map.imag, mask=mask)
xoff_masked = off_map.real.copy()
yoff_masked = off_map.imag.copy()
xoff_masked[mask] = 0
yoff_masked[mask] = 0

# - Run as 5x5 median filter to locate isolated offsets values - offsets
# - surrounded by zeros and set them to zero.
# - Find more details in step2 of off_filter.pro

# xoff_masked.mask \
#     = (xoff_masked.mask
#        | (medfilt(xoff_masked.filled(fill_value=0), 5) == 0)
#        | (medfilt(yoff_masked.filled(fill_value=0), 5) == 0))
#
# yoff_masked.mask\
#     = (yoff_masked.mask
#        | (medfilt(xoff_masked.filled(fill_value=0), 5) == 0)
#        | (medfilt(yoff_masked.filled(fill_value=0), 5) == 0))

g_mask = mask | (medfilt(xoff_masked, 5) == 0) | (medfilt(yoff_masked, 5) == 0)

xoff_masked[g_mask] = np.nan
yoff_masked[g_mask] = np.nan

xoff_masked = medfilt(xoff_masked, 3)
yoff_masked = medfilt(yoff_masked, 3)

# w = np.where(np.isnan(xoff_masked) or np.isnan(yoff_masked))
# xoff_masked[w] = 0
# yoff_masked[w] = 0


# - Apply Median Filter
# xoff_masked = medfilt(xoff_masked.filled(fill_value=0), 3)
# yoff_masked = medfilt(yoff_masked.filled(fill_value=0), 3)

# - Smooth Offsets
smth_kernel_size = 7
kernel = Box2DKernel(smth_kernel_size)

if smooth:
    xoff_masked \
        = convolve(xoff_masked, kernel, boundary='extend')
    yoff_masked \
        = convolve(yoff_masked, kernel, boundary='extend')
else:
    # xoff_masked = xoff_masked.filled(fill_value=np.nan)
    # yoff_masked = yoff_masked.filled(fill_value=np.nan)
    pass

# - Set to Zero offsets pixels that have a zero value in one of the
# - two directions.
ind_zero = np.where((xoff_masked == 0) | (yoff_masked == 0))
xoff_masked[ind_zero] = np.nan
yoff_masked[ind_zero] = np.nan

# - Fill Missing Values
fill = True
if fill:
    print('# - Filling Gaps Offsets Map by interpolation.')
    x_mask = np.ones(np.shape(xoff_masked))
    x_mask[np.where(np.isnan(xoff_masked))] = 0
    xoff_masked = fill_nodata(xoff_masked, x_mask,
                              max_search_dist=1000, smth_iter=10)
    y_mask = np.ones(np.shape(yoff_masked))
    y_mask[np.where(np.isnan(yoff_masked))] = 0
    yoff_masked = fill_nodata(yoff_masked, y_mask,
                              max_search_dist=1000, smth_iter=10)

    # - Jeremie Outlier fillinig strategy
    # - set NaNs to zero
    w_ind = np.where(np.isnan(yoff_masked))
    loop = 0
    smth_kernel_size = 15
    f_kernel = Box2DKernel(smth_kernel_size)

    while len(w_ind[0]) >= 100 and loop <= 100:
        print(len(w_ind[0]))
        loop += 1
        # - x-offsets
        # l_ind = np.where((xoff_masked == 0))
        # l_ind = np.where(np.isnan(xoff_masked))
        if len(w_ind[0]) >= 0:
            # xoff_masked[l_ind] = np.nan
            xoff_f_temp = convolve(xoff_masked, f_kernel, boundary='extend')
            # s_ind = np.where(np.isnan(xoff_masked))
            # xoff_masked[s_ind] = xoff_f_temp[s_ind]
            xoff_masked[w_ind] = xoff_f_temp[w_ind]
            xoff_f_temp = None
            # f_ind = np.where(np.isnan(xoff_masked))

        # # - y-offsets
        # w_ind = np.where((yoff_masked == 0))
        # if len(w_ind[0]) > 0:
            # yoff_masked[w_ind] = np.nan
            yoff_f_temp = convolve(yoff_masked, f_kernel, boundary='extend')
            # s_ind = np.where(np.isnan(yoff_masked))
            # yoff_masked[s_ind] = yoff_f_temp[s_ind]
            yoff_masked[w_ind] = yoff_f_temp[w_ind]
            yoff_f_temp = None
            w_ind = np.where(np.isnan(yoff_masked))

# - Subtract Polynomial Ramp from Offsets Map
xoff_masked -= ramp_offx
yoff_masked -= ramp_offy

# - Regrid Masked Offsets to the Selected Resolution.
print('# - Interpolating Offsets to Interferogram Grid.')
print(f'# - Input Offsets Grid Shape: [{poff.nrec},{poff.npix}]')
poff.nrec = int(poff.nrec / poff.azsp * azimuth_spacing)
poff.npix = int(poff.npix / poff.rgsp * range_spacing)

print(f'# - Interferogram Grid Shape: [{poff.nrec},{poff.npix}]')
poff.rgsp = range_spacing
poff.azsp = azimuth_spacing
poff.x_end = poff.x_start + (poff.npix - 1) * poff.rgsp
poff.y_end = poff.y_start + (poff.nrec - 1) * poff.azsp

# - Interpolate Offsets to Interferogram Grid
xoff_masked[np.isnan(xoff_masked)] = 0
yoff_masked[np.isnan(yoff_masked)] = 0
x_off = congrid2d(xoff_masked, [poff.nrec, poff.npix], NoData=0)
y_off = congrid2d(yoff_masked, [poff.nrec, poff.npix], NoData=0)

# - Save Offsets as a complex array
off_masked = x_off + 1j * y_off
off_masked.byteswap()\
    .tofile(os.path.join(data_dir, id1 + '-' + id2
                         + '.offmap.off.new.interp'))
# - Save Interpolated Offsets Parameters
poff.write(os.path.join(data_dir, id1 + '-' + id2 + '.offmap.par.interp'))

plt.figure(figsize=(4, 7))
plt.imshow(np.angle(off_masked), cmap=plt.get_cmap('twilight'),
           interpolation='none')
plt.tight_layout()
plt.savefig(os.path.join(data_dir, id1 + '-' + id2 + '.offmap_test.png'))
