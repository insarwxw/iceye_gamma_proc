# - Python Dependencies
import os


def path_to_dem(dem: str) -> dict:
    """
    Return absolute path to selected DEM and its parameter files.
    :param dem: DEM name.
    :return: dictionary with absolute paths to DEM and its parameter files.
    """
    # dem_path = os.environ['DAT_PATH']   # - DAT_PATH
    dem_path = os.environ['PYTHONDATA']   # - DAT_PATH
    # - Get absolute path to DEM and its parameter files
    if dem.lower() in ['gis', 'gimp', 'greenland']:
        # - GIMP DEM
        return {'path': os.path.join(dem_path, 'GREENLAND', 'DEM'),
                'dem': 'gimpdem100.dat',    # - DEM binary
                'par': 'DEM_gc_par',        # - DEM parameters
                'oversample': 10,           # - DEM oversampling factor
                }
    elif dem.lower() in ['ais', 'antarctica', 'bedmap2']:
        # - BEDMAP2 DEM
        # dem_path = os.environ['PYTHONDATA']
        # return {#'path': os.path.join(dem_path, 'ANTARCTICA', 'DEM', 'BEDMAP2'),
        #         'path': os.path.join(dem_path, 'bedmap2'),
        #         'dem': 'bedmap2_surface.dat',   # - DEM binary
        #         'par': 'DEM_gc_par',            # - DEM parameters
        #         'oversample': 100,              # - DEM oversampling factor
        #         }
        return {
            # - Path to DEM directory
            # 'path': os.path.join(dem_path, 'ANTARCTICA',
            #                      'DEM', 'TanDEM-X_500m'),
            'path': os.path.join(dem_path, 'TanDEM-X_500m'),
            # - DEM binary
            'dem': 'TDX_DEM_500m.filtered.ASTER_PEN.BEDMAP2.v2.dat',
            'par': 'DEM_gc_par',            # - DEM parameters
            'oversample': 50,               # - DEM oversampling factor
            }
    else:
        raise ValueError(f'Unknown DEM selected: {dem}')
