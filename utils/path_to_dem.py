# - Python Dependencies
import os


def path_to_dem(dem: str) -> dict:
    """
    Return absolute path to selected DEM and its parameter files.
    :param dem: DEM name.
    :return: dictionary with absolute paths to DEM and its parameter files.
    """
    if dem.lower() in ['gis', 'gimp', 'greenland']:
        # - GIMP DEM
        return {'path': os.path.join(os.environ['DAT_PATH'],
                                     'GREENLAND', 'DEM'),
                'dem': 'gimpdem100.dat',
                'par': 'DEM_gc_par',
                }
    elif dem.lower() in ['ais', 'antarctica', 'bedmap2']:
        # - Bedmap2 DEM
        return {'path': os.path.join(os.environ['DAT_PATH'],
                                     'ANTARCTICA', 'DEM', 'BEDMAP2'),
                'dem': 'bedmap2_surface.dat',
                'par': 'DEM_gc_par',
                }
    else:
        raise ValueError(f'Unknown DEM selected: {dem}')
