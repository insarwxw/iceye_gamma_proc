# - Python Dependencies
import os


def path_to_gimp():
    """
    Return absolute path to GIMP DEM and its parameter files.
    :return: str
    """
    return os.path.join(os.environ['DAT_PATH'], 'GREENLAND', 'DEM')
