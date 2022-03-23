# - Python Dependencies
import os


def psfilt(igram: str, igram_width: int) -> None:
    """
    Applu PSfilter to the input interferogram
    :param igram: input interferogram
    :param igram_width: input interferogram width
    :return: None
    """
    os.system('/u/pennell-z0/eric/ST_RELEASE/GAMMA/Util/psfilt/psfilt ' +
              f'{igram} {igram}.psfilt {igram_width}')
