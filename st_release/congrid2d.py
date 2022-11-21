from osgeo import gdal, osr
import numpy as np


def congrid2d(a, newdims, NoData=None, method='bilinear'):
    npix0 = a.shape[1]
    nrec0 = a.shape[0]

    datatype = a.dtype
    if datatype is np.dtype(np.complex64):
        gdaltype = gdal.GDT_CFloat32
    elif datatype is np.dtype(np.float64):
        gdaltype = gdal.GDT_Float64
    elif datatype is np.dtype(np.float32):
        gdaltype = gdal.GDT_Float32
    elif datatype is np.dtype(np.int16):
        gdaltype = gdal.GDT_Int16
    elif datatype is np.dtype(np.int32):
        gdaltype = gdal.GDT_Int32
    elif datatype is np.dtype(np.byte):
        gdaltype = gdal.GDT_Byte
    else:
        gdaltype = gdal.GDT_Float32

    im0 = gdal.GetDriverByName('MEM').Create('', int(npix0), int(nrec0),
                                             1, gdaltype)

    # xmin, xposting, 0 ymax, 0, yposting
    im0.SetGeoTransform((0, 1, 0, nrec0, 0, -1))
    im0.SetMetadataItem("AREA_OR_POINT", "Point", "")
    if NoData is not None:
        im0.GetRasterBand(1).SetNoDataValue(NoData)
    im0.GetRasterBand(1).WriteArray(a)

    npix1 = newdims[1]
    nrec1 = newdims[0]

    im1 \
        = gdal.GetDriverByName('MEM').Create('', int(npix1),
                                             int(nrec1), 1, gdaltype)

    xspacing = float(npix0) / float(npix1)
    yspacing = float(nrec0) / float(nrec1)
    im1.SetGeoTransform((0, xspacing, 0, nrec0, 0, -yspacing))
    if NoData is not None:
        im1.GetRasterBand(1).SetNoDataValue(NoData)

    if method == 'average':
        gdalresampling = gdal.GRA_Average
    elif method == 'bilinear':
        gdalresampling = gdal.GRA_Bilinear
    elif method == 'cubic':
        gdalresampling = gdal.GRA_Cubic
    elif method == 'cubicspline':
        gdalresampling = gdal.GRA_CubicSpline
    elif method == 'lanczos':
        gdalresampling = gdal.GRA_Lanczos
    elif method == 'mode':
        gdalresampling = gdal.GRA_Mode
    elif method == 'nearest':
        gdalresampling = gdal.GRA_NearestNeighbor
    else:
        gdalresampling = gdal.GRA_Bilinear

    source = osr.SpatialReference()
    gdal.ReprojectImage(im0, im1, source.ExportToWkt(), source.ExportToWkt(),
                        gdalresampling)
    del im0

    return im1.GetRasterBand(1).ReadAsArray()




