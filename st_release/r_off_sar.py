import numpy as np
import os
import py_gamma as pg
from fparam import off_param, isp_param


def r_off_sar(id1: str, id2: str) -> None:

    # - Reference Offsets Map
    off_in = id1 + '-' + id2 + '.offmap_1.in'
    # - Full Offsets Map Name
    off_map = 'off.off'

    with open(off_in, 'r') as f:
        lines = f.readlines()
    # - Read Offset Map Parameters
    y_posting = np.int32((lines[4].split()[2]))
    x_posting = np.int32((lines[5].split()[2]))
    r0 = np.int32((lines[9].split()[0]))
    z0 = np.int32((lines[9].split()[1]))
    ofw_w = np.int32((lines[6].split()[0]))
    ofw_h = np.int32((lines[6].split()[1]))

    # - If previously calculated summary offset map exists, delete it
    if os.path.isfile(os.path.join('.', off_map)):
        os.remove(os.path.join('.', off_map))
    # - Compute a new offset summary
    os.system("ls " + id1 + "-" + id2 + ".offmap_?  | xargs cat | grep -v '*' |"
                                        " awk 'length($0)>80' >> off.off")
    os.system("ls " + id1 + "-" + id2 + ".offmap_??  | xargs cat | grep -v '*'"
                                        " | awk 'length($0)>80' >> off.off")

    # -
    if os.stat(off_map).st_size < 830:
        print('Too few lines in off.off. File is (almost) empty..')
        return

    try:
        x, offx, y, offy, snr0, _, _, _ = np.loadtxt('off.off', unpack=True)
    except:
        print('Something wrong with off.off (offsetmap)')
        return

    xmin = min(x)
    xmax = max(x)
    ymin = min(y)
    ymax = max(y)

    print('xmin, xmax, ymin, ymax')
    print(xmin, xmax, ymin, ymax)

    n_pix = np.int32((xmax - xmin) / x_posting) + 1
    n_rec = np.int32((ymax - ymin) / y_posting) + 1

    print(f'Offset map dimensions: [{n_pix}, {n_rec}]')

    # - x and y axis are transposed compared to IDL
    off = np.zeros([n_rec, n_pix], dtype=np.complex64)

    x = np.int32((x - xmin) / x_posting)
    y = np.int32((y - ymin) / y_posting)

    off[y, x] = offx + offy * 1j

    snr = np.zeros([n_rec, n_pix], dtype=np.float32)
    snr[y, x] = snr0

    # - Load ISP parameters
    p1 = isp_param()
    p1.load(id1 + '.par')

    # - Load Offset Parameters
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

    p1 = isp_param()
    p1.load(id1 + '.par')

    poff.write(id1 + '-' + id2 + '.offmap.par')

    print('Save off ..')
    print('dtype off:', off.dtype)
    with open(id1 + '-' + id2 + '.offmap.off', 'w') as f_out:
        off.byteswap().tofile(f_out)

    print('Save snr ..')
    with open(id1 + '-' + id2 + '.offmap.snr', 'w') as s_out:
        snr.byteswap().tofile(s_out)

    pg.offset_fit('offset_fit ' + id1 + '-' + id2 + '.offmap.off',
                  id1 + '-' + id2 + '.offmap.snr',
                  id1 + '-' + id2 + '.offmap.par',
                  'to', 't1', '-', '3')
    # cmd = 'offset_fit ' + id1 + '-' + id2 + '.offmap.off ' + id1 + '-' + id2 + '.offmap.snr ' + id1 + '-' + id2 + '.offmap.par to t1 - 3'
    # print(cmd)
    # os.system(cmd)

    # cmd = 'offset_sub ' + id1 + '-' + id2 + '.offmap.off ' + id1 + '-' + id2 + '.offmap.par ' + id1 + '-' + id2 + '.offmap.off.new'
    # print(cmd)
    # try:
    #     os.system(
    #         '/u/mawson-r0/eric/GAMMA/GAMMA_SOFTWARE-20190613/ISP/bin/' + cmd)
    # except:
    #     # offset_sub does not exist on the default gamma installation path
    #     os.system(
    #         '/u/mawson-r0/eric/GAMMA/GAMMA_SOFTWARE-20190613/ISP/bin/' + cmd)
    pg.offset_sub('offset_sub ' + id1 + '-' + id2 + '.offmap.off',
                  id1 + '-' + id2 + '.offmap.par',
                  id1 + '-' + id2 + '.offmap.off.new')

    # cmd = 'rasmph ' + id1 + '-' + id2 + '.offmap.off.new ' + str(
    #     poff.npix) + ' - - - - - - - ' + id1 + '-' + id2 + '.offmap.off.new.bmp'
    # print(cmd)
    # os.system(cmd)
    pg.rasmph('rasmph ' + id1 + '-' + id2 + '.offmap.off.new',
              str(poff.npix), '-', '-', '-', '-', '-', '-', '-',
              id1 + '-' + id2 + '.offmap.off.new.bmp')

    # cmd = 'rm ' + id1 + '-' + id2 + '.offmap.off.new'
    # print(cmd)
    # os.system(cmd)
    os.remove(id1 + '-' + id2 + '.offmap.off.new')

    return




