# - Python Dependencies
import os


def path_to_ampcor():
    """
    Return absolute path to directory containing AMPCOR binaries.
    :return: str
    """
    return os.path.join(os.path.expanduser("~"),
                        'code.dir', 'ampcor_binary_z')
