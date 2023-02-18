#!/usr/bin/env python
"""
Written by Enrico Ciraci' - 12/2022
Return absolute path to selected DEM and its parameter files.
"""
# - Python Dependencies
import os


def path_to_dem(dem: str, oversample: int = 1) -> dict:
    """
    Return absolute path to selected DEM and its parameter files.
    :param dem: DEM name.
    :param oversample: DEM oversampling rate
    :return: dictionary with absolute paths to DEM and its parameter files.
    """
    # - Get absolute path to DAT_PATH
    dem_path = os.environ['DAT_PATH']   # - DAT_PATH
    # - Get absolute path to DEM and its parameter files
    if dem.lower() in ['gis', 'gimp', 'greenland']:
        # - GIMP DEM
        return {'path': os.path.join(dem_path, 'GREENLAND', 'DEM'),
                'dem': 'gimpdem100.dat',    # - DEM binary
                'par': 'DEM_gc_par',        # - DEM parameters
                'oversample': oversample,           # - DEM oversampling factor
                }
    elif dem.lower() in ['bedmap2']:
        # - BEDMAP2 DEM
        return {
                'path': os.path.join(dem_path, 'ANTARCTICA', 'DEM', 'BEDMAP2'),
                'dem': 'bedmap2_surface.dat',   # - DEM binary
                'par': 'DEM_gc_par',            # - DEM parameters
                'oversample': oversample,        # - DEM oversampling factor
                }
    elif dem.lower() in ['tdx_500m', 'tdx']:
        return {
            # - Path to DEM directory
            'path': os.path.join(dem_path, 'ANTARCTICA',
                                 'DEM', 'TanDEM-X_500m'),
            # 'path': os.path.join(dem_path, 'TanDEM-X_500m'),
            # - DEM binary
            'dem': 'TDX_DEM_500m.filtered.ASTER_PEN.BEDMAP2.v2.dat',
            'par': 'DEM_gc_par',            # - DEM parameters
            'oversample': oversample,       # - DEM oversampling factor
            }
    elif dem.lower() in ['rema', 'worldview']:
        dem_path = os.environ['PYTHONDATA']  # - PYTHONDATA
        return {
            # - Path to DEM directory
            'path': os.path.join(dem_path, 'REMA'),
            # - DEM binary
            'dem': 'REMA_merge_3031.dat',
            'par': 'DEM_gc_par',  # - DEM parameters
            'oversample': oversample,  # - DEM oversampling factor
            }
    else:
        raise ValueError(f'Unknown DEM selected: {dem}')
