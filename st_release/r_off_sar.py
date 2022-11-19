import numpy as np
import os
import py_gamma as pg
from st_release.fparam import off_param, isp_param


def r_off_sar(data_dir: str, id1: str, id2: str, poly_order: int = 3) -> None:

    # - Load the firs available offset parameter file and
    # - extract AMPCOR calculation parameters.
    off_in = os.path.join(data_dir, id1 + '-' + id2 + '.offmap_1.in')

    # - Full Domain Offsets Map file name
    off_map_name = 'full_offsets_map.off'
    off_map_path = os.path.join(data_dir, 'full_offsets_map.off')

    with open(off_in, 'r') as f:
        lines = f.readlines()

    # - Read Offsets Map Parameters
    y_posting = np.int32((lines[4].split()[2]))
    x_posting = np.int32((lines[5].split()[2]))
    r0 = np.int32((lines[9].split()[0]))
    z0 = np.int32((lines[9].split()[1]))
    ofw_w = np.int32((lines[6].split()[0]))
    ofw_h = np.int32((lines[6].split()[1]))

    # - If previously calculated summary offset map exists, delete it
    if os.path.isfile(off_map_path):
        os.remove(off_map_path)

    # - Concatenate all available offset files content into a single file
    os.system("ls " + os.path.join(data_dir, id1 + "-" + id2 + ".offmap_?")
              + "  | xargs cat | grep -v '*' |"
                f" awk 'length($0)>80' >> {off_map_path}")
    os.system("ls " + os.path.join(data_dir, id1 + "-" + id2 + ".offmap_??")
              + "  | xargs cat | grep -v '*' "
                f"| awk 'length($0)>80' >> {off_map_path}")

    # - Verify that the concatenated file has the right format.
    if os.stat(off_map_path).st_size < 830:
        raise ValueError(f"Too few lines in {off_map_name}. "
                         f"File is (almost) empty.")

    # - Unpack Offsets Map
    x, offx, y, offy, snr0, _, _, _ = np.loadtxt(off_map_path, unpack=True)
    # try:
    #     x, offx, y, offy, snr0, _, _, _ = np.loadtxt(off_map_path, unpack=True)
    # except:
    #     # - Not really clear what exception this operation is supposed to catch
    #     print('Something wrong with off.off (offsetmap)')
    #     return

    # - Evaluate Offsets Domain extremes
    xmin = min(x)
    xmax = max(x)
    ymin = min(y)
    ymax = max(y)
    print('# - Offsets Domain Extremes:')
    print(f'# - xmin: {xmin}, xmax: {xmax}, ymin: {ymin}, ymax: {ymax}')

    # - Compute Total Offsets Map Dimensions
    n_pix = np.int32((xmax - xmin) / x_posting) + 1
    n_rec = np.int32((ymax - ymin) / y_posting) + 1
    print(f'Offset map dimensions: [{n_pix}, {n_rec}]')

    # - Columns and rows are transposed compared to IDL
    off_map = np.zeros([n_rec, n_pix], dtype=np.complex64)
    # - off_map index values
    x = np.int32((x - xmin) / x_posting)
    y = np.int32((y - ymin) / y_posting)
    # - Fill the Offsets Map [Note: Complex Offsets]
    off_map[y, x] = offx + offy * 1j
    # - Offsets Signal to Noise Ratio Map
    snr_map = np.zeros([n_rec, n_pix], dtype=np.float32)
    snr_map[y, x] = snr0

    # - Load Reference SLC ISP parameters
    p1 = isp_param()
    p1.load(os.path.join(data_dir, id1 + '.par'))

    # - Generate Offsets Map Parameters File
    poff = off_param()
    poff.r0 = np.int32(r0)
    poff.z0 = np.int32(z0)
    poff.snpix = np.int32(p1.npix)
    poff.x_start = np.int32(xmin)
    poff.x_end = np.int32(xmin + (n_pix - 1) * x_posting)
    poff.npix = np.int32(n_pix)
    poff.rgsp = np.int32(x_posting)
    poff.y_start = np.int32(ymin)
    poff.y_end = np.int32(ymin + (n_rec - 1) * y_posting)
    poff.nrec = np.int32(n_rec)
    poff.azsp = np.int32(y_posting)
    poff.ofw_w = np.int32(ofw_w)
    poff.ofw_h = np.int32(ofw_h)
    poff.ofw_thr = 3
    poff.xoff[0] = r0
    poff.yoff[0] = z0
    # - x_posting, y_posting is in pixel not meters
    poff.nrec_i = np.int32(p1.nrec / y_posting)
    poff.npix_i = np.int32(p1.npix / x_posting)
    poff.xnlook = x_posting
    poff.ynlook = y_posting
    poff.rgsp_i = x_posting * p1.rgsp
    poff.azsp_i = y_posting * p1.azsp

    # - Update Offsets Parameter File Content
    poff.write(os.path.join(data_dir, id1 + '-' + id2 + '.offmap.par'))

    print(f'# - Save {off_map_name}')
    print(f'# - {off_map_name} data type :', off_map.dtype)
    with open(os.path.join(data_dir, id1 + '-' + id2 + '.offmap.off'),
              'w') as f_out:
        off_map.byteswap().tofile(f_out)

    print('# - Save SNR.')
    with open(os.path.join(data_dir, id1 + '-' + id2 + '.offmap.snr'),
              'w') as s_out:
        snr_map.byteswap().tofile(s_out)

    # - Run Gamma offset_fit: Range and azimuth offset polynomial estimation
    pg.offset_fit(os.path.join(data_dir, id1 + '-' + id2 + '.offmap.off'),
                  os.path.join(data_dir, id1 + '-' + id2 + '.offmap.snr'),
                  os.path.join(data_dir, id1 + '-' + id2 + '.offmap.par'),
                  os.path.join(data_dir, 'coffs'),
                  os.path.join(data_dir, 'coffsets'), '-', poly_order, 0)

    # - Run Gamma offset_sub: Subtraction of polynomial
    # - from range and azimuth offset estimates
    pg.offset_sub(os.path.join(data_dir, id1 + '-' + id2 + '.offmap.off '),
                  os.path.join(data_dir, id1 + '-' + id2 + '.offmap.par'),
                  os.path.join(data_dir, id1 + '-' + id2 + '.offmap.off.new'))

    # - Run GAMMA rasmph: Generate 8-bit raster graphics image of the phase
    # - and intensity of complex data
    pg.rasmph(os.path.join(data_dir, id1 + '-' + id2 + '.offmap.off.new'),
              poff.npix, '-', '-', '-', '-', '-', '-', '-',
              os.path.join(data_dir, id1 + '-' + id2 + '.offmap.off.new.bmp'))

    # - Remove temporary offset map obtained using Gamma offset_sub
    os.remove(os.path.join(data_dir, id1 + '-' + id2 + '.offmap.off.new'))

    return




