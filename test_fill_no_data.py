import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
from xrspatial import generate_terrain
from st_release.fill_nodata import fill_nodata

W = 800
H = 600
terrain = xr.DataArray(np.zeros((H, W)))
terrain = generate_terrain(terrain)
terrain_arr = terrain.values
terrain_arr[100:300, 300: 400] = np.nan

plt.imshow(terrain_arr)
plt.colorbar()
plt.show()

mask = np.ones(np.shape(terrain_arr))
mask[np.where(np.isnan(terrain_arr))] = 0

filled_terrain = fill_nodata(terrain_arr, mask)
plt.imshow(filled_terrain)
plt.show()