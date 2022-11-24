import numpy as np
from st_release.read_keyword import read_keyword


class geo_param:  # {{{

    def __init__(self, utm=False):  # {{{

        self.title = ''
        self.data_format = ''

        self.ymax = 0.
        self.xmin = 0.
        self.nrec = 0.
        self.npix = 0.
        self.xposting = 0.
        self.yposting = 0.
        self.posting = 0.
        self.srs = None

        if utm:
            self.projection = 'UTM'
            self.projection_zone = 0
            self.false_easting = 0.0
            self.false_northing = 0.0
        else:
            self.projection = 'PS'
            self.central_meridian = 0.
            self.secant_lat = 0.

    # }}}
    def load_greenland(self):  # {{{

        self.title = 'Default Grid for Greenland'
        self.projection = 'PS'
        self.ymax = np.float64(-657600.0)
        self.xmin = np.float64(-638000.0)
        self.xposting = np.float64(150.000)
        self.yposting = np.float64(-150.000)
        self.posting = np.float64(150.000)
        self.ellipsoid_name = 'WGS 84'
        self.ellipsoid_ra = 6378137.000
        self.ellipsoid_reciprocal_flattening = 298.2572236
        self.secant_lat = 70.000000
        self.central_meridian = -45.000000
        self.npix = 10018
        self.nrec = 17946

    # }}}
    def load(self, f='DEM_gc_par'):  # {{{

        self.title = read_keyword(f, 'title')
        self.data_format = read_keyword(f, 'data_format')
        self.projection = read_keyword(f, 'DEM_projection')
        self.DEM_hgt_offset = np.float64(read_keyword(f, 'DEM_hgt_offset'))
        self.DEM_scale = np.float64(read_keyword(f, 'DEM_scale'))

        if read_keyword(f, 'corner_north', rm_unit='m') == '-1':
            self.ymax = np.float64(
                read_keyword(f, 'PS_corner_north', rm_unit='m'))
        else:
            self.ymax = np.float64(read_keyword(f, 'corner_north', rm_unit='m'))

        if read_keyword(f, 'corner_east', rm_unit='m') == '-1':
            self.xmin = np.float64(
                read_keyword(f, 'PS_corner_east', rm_unit='m'))
        else:
            self.xmin = np.float64(read_keyword(f, 'corner_east', rm_unit='m'))

        self.nrec = np.int32(read_keyword(f, 'nlines'))
        self.npix = np.int32(read_keyword(f, 'width'))

        if read_keyword(f, 'post_east', rm_unit='m') == '-1':
            self.xposting = np.float64(
                read_keyword(f, 'PS_post_east', rm_unit='m'))
        else:
            self.xposting = np.float64(
                read_keyword(f, 'post_east', rm_unit='m'))

        if read_keyword(f, 'post_north', rm_unit='m') == '-1':
            self.yposting = np.float64(
                read_keyword(f, 'PS_post_north', rm_unit='m'))
        else:
            self.yposting = np.float64(
                read_keyword(f, 'post_north', rm_unit='m'))

        self.posting = self.xposting

        self.ellipsoid_name = 'WGS 84'
        self.ellipsoid_ra = 6378137.000
        self.ellipsoid_reciprocal_flattening = 298.2572236

        self.datum_name = read_keyword(f, 'datum_name')
        self.datum_shift_dx = np.float64(
            read_keyword(f, 'datum_shift_dx', rm_unit='m'))
        self.datum_shift_dy = np.float64(
            read_keyword(f, 'datum_shift_dy', rm_unit='m'))
        self.datum_shift_dz = np.float64(
            read_keyword(f, 'datum_shift_dz', rm_unit='m'))
        self.datum_scale_m = np.float64(read_keyword(f, 'datum_scale_m'))
        self.datum_rotation_alpha = np.float64(
            read_keyword(f, 'datum_rotation_alpha', rm_unit='arc-sec'))
        self.datum_rotation_beta = np.float64(
            read_keyword(f, 'datum_rotation_beta', rm_unit='arc-sec'))
        self.datum_rotation_gamma = np.float64(
            read_keyword(f, 'datum_rotation_gamma', rm_unit='arc-sec'))
        self.datum_country_list = 'Global Definition, WGS84, World'

        if self.projection == 'UTM':

            self.projection_name = read_keyword(f, 'projection_name')
            self.projection_zone = np.int32(read_keyword(f, 'projection_zone'))
            self.false_easting = np.float64(
                read_keyword(f, 'false_easting', rm_unit='m'))
            self.false_northing = np.float64(
                read_keyword(f, 'false_northing', rm_unit='m'))
            self.projection_k0 = np.float64(
                read_keyword(f, 'projection_k0', rm_unit='m'))
            self.center_longitude = np.float64(
                read_keyword(f, 'center_longitude', rm_unit='decimal degrees'))
            if self.center_longitude > 180:
                self.center_longitude = self.center_longitude - 360.
            self.center_latitude = np.float64(
                read_keyword(f, 'center_latitude', rm_unit='decimal degrees'))

        else:
            self.secant_lat = np.float64(
                read_keyword(f, 'PS_secant_lat', rm_unit='decimal degrees'))
            self.central_meridian = np.float64(
                read_keyword(f, 'PS_central_meridian',
                             rm_unit='decimal degrees'))

    # }}}
    def write(self, f='DEM_gc_par'):  # {{{

        lun = open(f, 'w')
        lun.write('Gamma DIFF&GEO DEM/MAP parameter file' + '\n')
        lun.write('title: ' + self.title + '\n')
        lun.write('DEM_projection:     ' + self.projection + '\n')
        lun.write('data_format:        ' + self.data_format + '\n')
        lun.write('DEM_hgt_offset:          0.00000' + '\n')
        lun.write('DEM_scale:               1.00000' + '\n')
        lun.write('width:        ' + str(self.npix) + '\n')
        lun.write('nlines:       ' + str(self.nrec) + '\n')
        lun.write(
            'corner_north:' + '{:22.3f}'.format(self.ymax) + '   m' + '\n')
        lun.write('corner_east:' + '{:22.3f}'.format(self.xmin) + '   m' + '\n')
        lun.write(
            'post_north:' + '{:15.5f}'.format(self.yposting) + '   m' + '\n')
        lun.write(
            'post_east:' + '{:15.5f}'.format(self.xposting) + '   m' + '\n')

        if self.projection == 'PS':
            lun.write('PS_secant_lat:      ' + '{:13.6f}'.format(
                self.secant_lat) + '   decimal degrees' + '\n')
            lun.write('PS_central_meridian:' + '{:13.6f}'.format(
                self.central_meridian) + '   decimal degrees' + '\n')

        lun.write('' + '\n')
        lun.write('ellipsoid_name: WGS 84' + '\n')
        lun.write('ellipsoid_ra:        6378137.000   m' + '\n')
        lun.write('ellipsoid_reciprocal_flattening:  298.2572236' + '\n')
        lun.write('' + '\n')
        lun.write('datum_name: WGS 1984' + '\n')
        lun.write('datum_shift_dx:              0.000   m' + '\n')
        lun.write('datum_shift_dy:              0.000   m' + '\n')
        lun.write('datum_shift_dz:              0.000   m' + '\n')
        lun.write('datum_scale_m:         0.00000e+00' + '\n')
        lun.write('datum_rotation_alpha:  0.00000e+00   arc-sec' + '\n')
        lun.write('datum_rotation_beta:   0.00000e+00   arc-sec' + '\n')
        lun.write('datum_rotation_gamma:  0.00000e+00   arc-sec' + '\n')
        lun.write('datum_country_list: Global Definition, WGS84, World' + '\n')

        if self.projection == 'UTM':
            lun.write('' + '\n')
            lun.write('projection_name: UTM' + '\n')
            lun.write('projection_zone:             ' + str(
                self.projection_zone) + '\n')
            lun.write('false_easting:           ' + str(
                self.false_easting) + '   m' + '\n')
            lun.write('false_northing:          ' + str(
                self.false_northing) + '   m' + '\n')
            lun.write('projection_k0:            0.9996000' + '\n')
            lun.write(
                'center_longitude:         0.0000000   decimal degrees' + '\n')
            lun.write(
                'center_latitude:          0.0000000   decimal degrees' + '\n')

        lun.close()

    # }}}
    def describe(self):  # {{{

        print('Gamma DIFF&GEO DEM/MAP parameter file')
        print('title: ' + self.title)
        print('DEM_projection:     ' + self.projection)
        print('data_format:        ' + self.data_format)
        print('DEM_hgt_offset:          0.00000')
        print('DEM_scale:               1.00000')
        print('width:        ' + str(self.npix))
        print('nlines:       ' + str(self.nrec))
        print('corner_north:' + '{:22.3f}'.format(self.ymax) + '   m')
        print('corner_east:' + '{:22.3f}'.format(self.xmin) + '   m')
        print('post_north:' + '{:15.5f}'.format(self.yposting) + '   m')
        print('post_east:' + '{:15.5f}'.format(self.xposting) + '   m')

        if self.projection == 'PS':
            print('PS_secant_lat:      ' + '{:13.6f}'.format(
                self.secant_lat) + '   decimal degrees')
            print('PS_central_meridian:' + '{:13.6f}'.format(
                self.central_meridian) + '   decimal degrees')

        print('')
        print('ellipsoid_name: WGS 84')
        print('ellipsoid_ra:        6378137.000   m')
        print('ellipsoid_reciprocal_flattening:  298.2572236')
        print('')
        print('datum_name: WGS 1984')
        print('datum_shift_dx:              0.000   m')
        print('datum_shift_dy:              0.000   m')
        print('datum_shift_dz:              0.000   m')
        print('datum_scale_m:         0.00000e+00')
        print('datum_rotation_alpha:  0.00000e+00   arc-sec')
        print('datum_rotation_beta:   0.00000e+00   arc-sec')
        print('datum_rotation_gamma:  0.00000e+00   arc-sec')
        print('datum_country_list: Global Definition, WGS84, World')

        if self.projection == 'UTM':
            print('')
            print('projection_name: UTM')
            print('projection_zone:             ' + str(self.projection_zone))
            print('false_easting:           0.000   m')
            print('false_northing:          0.000   m')
            print('projection_k0:            0.9996000')
            print('center_longitude:         0.0000000   decimal degrees')
            print('center_latitude:          0.0000000   decimal degrees')

    # }}}
    def osr_spatial_reference(self):  # {{{
        from osgeo import osr

        t_srs = osr.SpatialReference()
        if self.projection == 'UTM':
            if self.projection_zone > 0:
                t_srs.ImportFromEPSG(
                    int('326' + '{:02d}'.format(self.projection_zone)))  # NORTH
                print('326' + '{:02d}'.format(self.projection_zone))
            else:
                t_srs.ImportFromEPSG(int('327' + '{:02d}'.format(
                    -self.projection_zone)))  # SOUTH
                print('327' + '{:02d}'.format(-self.projection_zone))
        elif self.projection == 'PS':
            if self.secant_lat == 70.0:
                # print('PS NORTH')
                t_srs.ImportFromEPSG(3413)
            else:
                # print('PS SOUTH')
                t_srs.ImportFromEPSG(3031)
        else:
            print(self.projection + ' not yet implemented...')

        t_srs.SetWellKnownGeogCS("WGS84")

        return t_srs
    # }}}


# }}}
class isp_param:  # {{{

    def __init__(self):
        self.title = ''
        self.sensor = ''
        self.date = np.zeros(6, np.float64)
        self.start_time = 0.
        self.center_time = 0.
        self.end_time = 0.
        self.azimuth_line_time = 0.
        self.line_header_size = 0
        self.npix = 0
        self.nrec = 0
        self.xnlook = 0
        self.ynlook = 0
        self.image_format = ''
        self.image_geometry = ''
        self.range_scale_factor = 0.
        self.azimuth_scale_factor = 0.
        self.center_latitude = 0.
        self.center_longitude = 0.
        self.heading = 0.
        self.rgsp = 0.
        self.azsp = 0.
        self.near_range_slc = 0.
        self.center_range_slc = 0.
        self.far_range_slc = 0.
        self.first_slant_range_polynomial = np.zeros(6, np.float64)
        self.center_slant_range_polynomial = np.zeros(6, np.float64)
        self.last_slant_range_polynomial = np.zeros(6, np.float64)
        self.incidence_angle = 0.
        self.azimuth_deskew = ''
        self.azimuth_angle = 0.
        self.radar_frequency = 0.
        self.adc_sampling_rate = 0.
        self.chirp_bandwidth = 0.
        self.prf = 0.
        self.azimuth_proc_bandwidth = 0.
        self.doppler_polynomial = np.zeros(4, np.float64)
        self.doppler_poly_dot = np.zeros(4, np.float64)
        self.doppler_poly_ddot = np.zeros(4, np.float64)
        self.receiver_gain = 0.
        self.calibration_gain = 0.
        self.sar_to_earth_center = 0.
        self.earth_radius_below_sensor = 0.
        self.earth_semi_major_axis = 0.
        self.earth_semi_minor_axis = 0.
        self.number_of_state_vectors = 15
        self.time_of_first_state_vector = 0.
        self.state_vector_interval = 0.
        self.state_vector_position = np.zeros([15, 3], np.float64)
        self.state_vector_velocity = np.zeros([15, 3], np.float64)

    def load(self, file):
        self.title = read_keyword(file, 'title')
        self.sensor = read_keyword(file, 'sensor')
        self.date = np.float64(read_keyword(file, 'date',
                                            multi_val=[' ', '0', '1', '2', '3',
                                                       '4', '5']))
        self.start_time = np.float64(
            read_keyword(file, 'start_time', rm_unit='s'))
        self.center_time = np.float64(
            read_keyword(file, 'center_time', rm_unit='s'))
        self.end_time = np.float64(read_keyword(file, 'end_time', rm_unit='s'))
        self.azimuth_line_time = np.float64(
            read_keyword(file, 'azimuth_line_time', rm_unit='s'))
        self.line_header_size = np.int32(read_keyword(file, 'line_header_size'))
        self.npix = np.int32(np.float64(read_keyword(file,
                                                     'range_samples')))  # 1st float then int - should be int but some files are wrong ...
        self.nrec = np.int32(np.float64(read_keyword(file, 'azimuth_lines')))
        self.xnlook = np.int32(read_keyword(file, 'range_looks'))
        self.ynlook = np.int32(read_keyword(file, 'azimuth_looks'))
        self.image_format = read_keyword(file, 'image_format')
        self.image_geometry = read_keyword(file, 'image_geometry')
        self.range_scale_factor = np.float64(
            read_keyword(file, 'range_scale_factor'))
        self.azimuth_scale_factor = np.float64(
            read_keyword(file, 'azimuth_scale_factor'))
        self.center_latitude = np.float64(
            read_keyword(file, 'center_latitude', rm_unit='degrees'))
        self.center_longitude = np.float64(
            read_keyword(file, 'center_longitude', rm_unit='degrees'))
        self.heading = np.float64(
            read_keyword(file, 'heading', rm_unit='degrees'))
        self.rgsp = np.float64(
            read_keyword(file, 'range_pixel_spacing', rm_unit='m'))
        self.azsp = np.float64(
            read_keyword(file, 'azimuth_pixel_spacing', rm_unit='m'))
        self.near_range_slc = np.float64(
            read_keyword(file, 'near_range_slc', rm_unit='m'))
        self.center_range_slc = np.float64(
            read_keyword(file, 'center_range_slc', rm_unit='m'))
        self.far_range_slc = np.float64(
            read_keyword(file, 'far_range_slc', rm_unit='m'))
        self.first_slant_range_polynomial = np.float64(
            read_keyword(file, 'first_slant_range_polynomial',
                         multi_val=[' ', '0', '1', '2', '3', '4', '5']))
        self.center_slant_range_polynomial = np.float64(
            read_keyword(file, 'center_slant_range_polynomial',
                         multi_val=[' ', '0', '1', '2', '3', '4', '5']))
        self.last_slant_range_polynomial = np.float64(
            read_keyword(file, 'last_slant_range_polynomial',
                         multi_val=[' ', '0', '1', '2', '3', '4', '5']))
        self.incidence_angle = np.float64(
            read_keyword(file, 'incidence_angle', rm_unit='degrees'))
        self.azimuth_deskew = read_keyword(file, 'azimuth_deskew')
        self.azimuth_angle = np.float64(
            read_keyword(file, 'azimuth_angle', rm_unit='degrees'))
        self.radar_frequency = np.float64(
            read_keyword(file, 'radar_frequency', rm_unit='Hz'))
        self.adc_sampling_rate = np.float64(
            read_keyword(file, 'adc_sampling_rate', rm_unit='Hz'))
        self.chirp_bandwidth = np.float64(
            read_keyword(file, 'chirp_bandwidth', rm_unit='Hz'))
        self.prf = np.float64(read_keyword(file, 'prf', rm_unit='Hz'))
        self.azimuth_proc_bandwidth = np.float64(
            read_keyword(file, 'azimuth_proc_bandwidth', rm_unit='Hz'))
        self.doppler_polynomial = np.float64(
            read_keyword(file, 'doppler_polynomial',
                         multi_val=[' ', '0', '1', '2', '3']))
        self.doppler_poly_dot = np.float64(
            read_keyword(file, 'doppler_poly_dot',
                         multi_val=[' ', '0', '1', '2', '3']))
        self.doppler_poly_ddot = np.float64(
            read_keyword(file, 'doppler_poly_ddot',
                         multi_val=[' ', '0', '1', '2', '3']))
        self.receiver_gain = np.float64(
            read_keyword(file, 'receiver_gain', rm_unit='dB'))
        self.calibration_gain = np.float64(
            read_keyword(file, 'calibration_gain', rm_unit='dB'))
        self.sar_to_earth_center = np.float64(
            read_keyword(file, 'sar_to_earth_center', rm_unit='m'))
        self.earth_radius_below_sensor = np.float64(
            read_keyword(file, 'earth_radius_below_sensor', rm_unit='m'))
        self.earth_semi_major_axis = np.float64(
            read_keyword(file, 'earth_semi_major_axis', rm_unit='m'))
        self.earth_semi_minor_axis = np.float64(
            read_keyword(file, 'earth_semi_minor_axis', rm_unit='m'))
        self.number_of_state_vectors = np.int32(
            read_keyword(file, 'number_of_state_vectors'))
        self.time_of_first_state_vector = np.float64(
            read_keyword(file, 'time_of_first_state_vector', rm_unit='s'))
        self.state_vector_interval = np.float64(
            read_keyword(file, 'state_vector_interval', rm_unit='s'))
        self.state_vector_position = np.zeros([self.number_of_state_vectors, 3],
                                              np.float64)
        self.state_vector_velocity = np.zeros([self.number_of_state_vectors, 3],
                                              np.float64)
        for i in range(0, self.number_of_state_vectors):
            self.state_vector_position[i, :] = np.float64(
                read_keyword(file, 'state_vector_position_' + str(i + 1),
                             multi_val=[' ', '0', '1', '2']))
            self.state_vector_velocity[i, :] = np.float64(
                read_keyword(file, 'state_vector_velocity_' + str(i + 1),
                             multi_val=[' ', '0', '1', '2']))

    def write(self, file):

        f = open(file, 'w')
        f.write(
            'Gamma Interferometric SAR Processor (ISP) - Image Parameter File\n')
        f.write('\n')
        f.write('title:     ' + self.title + '\n')
        f.write('sensor:    ' + self.sensor + '\n')
        f.write('date:      ' + '{:4d}'.format(int(self.date[0])) + ' ' + \
                '{:2d}'.format(int(self.date[1])) + ' ' + \
                '{:2d}'.format(int(self.date[2])) + ' ' + \
                '{:2d}'.format(int(self.date[3])) + ' ' + \
                '{:2d}'.format(int(self.date[4])) + ' ' + \
                '{:7.4f}'.format(self.date[5]) + '\n')
        f.write('start_time:             ' + '{:12.6f}'.format(
            self.start_time) + '   s' + '\n')
        f.write('center_time:            ' + '{:12.6f}'.format(
            self.center_time) + '   s\n')
        f.write('end_time:               ' + '{:12.6f}'.format(
            self.end_time) + '   s\n')
        f.write('azimuth_line_time:     ' + '{:13.7e}'.format(
            self.azimuth_line_time) + '   s\n')
        f.write('line_header_size:                  ' + str(
            self.line_header_size) + '\n')
        f.write('range_samples:                  ' + str(self.npix) + '\n')
        f.write('azimuth_lines:                ' + str(self.nrec) + '\n')
        f.write('range_looks:                       ' + str(self.xnlook) + '\n')
        f.write('azimuth_looks:                     ' + str(self.ynlook) + '\n')
        f.write('image_format:               ' + self.image_format + '\n')
        f.write('image_geometry:             ' + self.image_geometry + '\n')
        f.write('range_scale_factor:     ' + '{:13.7e}'.format(
            self.range_scale_factor) + '\n')
        f.write('azimuth_scale_factor:   ' + '{:13.7e}'.format(
            self.azimuth_scale_factor) + '\n')
        f.write('center_latitude:        ' + '{:12.7f}'.format(
            self.center_latitude) + '   degrees' + '\n')
        f.write('center_longitude:      ' + '{:13.7f}'.format(
            self.center_longitude) + '   degrees' + '\n')
        f.write('heading:                ' + '{:12.7f}'.format(
            self.heading) + '   degrees' + '\n')
        f.write('range_pixel_spacing:    ' + '{:12.6f}'.format(
            self.rgsp) + '   m' + '\n')
        f.write('azimuth_pixel_spacing:  ' + '{:12.6f}'.format(
            self.azsp) + '   m' + '\n')
        f.write('near_range_slc:           ' + '{:11.4f}'.format(
            self.near_range_slc) + '  m' + '\n')
        f.write('center_range_slc:         ' + '{:11.4f}'.format(
            self.center_range_slc) + '  m' + '\n')
        f.write('far_range_slc:            ' + '{:11.4f}'.format(
            self.far_range_slc) + '  m' + '\n')
        # WARNING should use values in self struct ...
        f.write(
            'first_slant_range_polynomial:        0.00000      0.00000  0.00000e+00  0.00000e+00  0.00000e+00  0.00000e+00  s m 1 m^-1 m^-2 m^-3' + '\n')
        f.write(
            'center_slant_range_polynomial:       0.00000      0.00000  0.00000e+00  0.00000e+00  0.00000e+00  0.00000e+00  s m 1 m^-1 m^-2 m^-3' + '\n')
        f.write(
            'last_slant_range_polynomial:         0.00000      0.00000  0.00000e+00  0.00000e+00  0.00000e+00  0.00000e+00  s m 1 m^-1 m^-2 m^-3' + '\n')
        f.write('incidence_angle:             ' + '{:7.4f}'.format(
            self.incidence_angle) + '   degrees' + '\n')
        f.write('azimuth_deskew:          ' + self.azimuth_deskew + '\n')
        f.write('azimuth_angle:               ' + '{:7.4f}'.format(
            self.azimuth_angle) + '   degrees' + '\n')
        f.write('radar_frequency:        ' + '{:13.7e}'.format(
            self.radar_frequency) + '   Hz' + '\n')
        f.write('adc_sampling_rate:      ' + '{:13.7e}'.format(
            self.adc_sampling_rate) + '   Hz' + '\n')
        f.write('chirp_bandwidth:        ' + '{:13.7e}'.format(
            self.chirp_bandwidth) + '   Hz' + '\n')
        f.write('prf:                     ' + '{:11.6f}'.format(
            self.prf) + '   Hz' + '\n')
        f.write('azimuth_proc_bandwidth:  ' + '{:11.5f}'.format(
            self.azimuth_proc_bandwidth) + '   Hz' + '\n')
        f.write('doppler_polynomial:      ' + '{:13.5e}'.format(
            self.doppler_polynomial[0]) + \
                '{:13.5e}'.format(self.doppler_polynomial[1]) + \
                '{:13.5e}'.format(self.doppler_polynomial[2]) + \
                '{:13.5e}'.format(self.doppler_polynomial[3]) + \
                '  Hz     Hz/m     Hz/m^2     Hz/m^3' + '\n')
        f.write('doppler_poly_dot:      ' + '{:13.5e}'.format(
            self.doppler_poly_dot[0]) + \
                '{:13.5e}'.format(self.doppler_poly_dot[1]) + \
                '{:13.5e}'.format(self.doppler_poly_dot[2]) + \
                '{:13.5e}'.format(self.doppler_poly_dot[3]) + \
                '  Hz/s   Hz/s/m   Hz/s/m^2   Hz/s/m^3' + '\n')
        f.write('doppler_poly_ddot:     ' + '{:13.5e}'.format(
            self.doppler_poly_ddot[0]) + \
                '{:13.5e}'.format(self.doppler_poly_ddot[1]) + \
                '{:13.5e}'.format(self.doppler_poly_ddot[2]) + \
                '{:13.5e}'.format(self.doppler_poly_ddot[3]) + \
                '  Hz/s^2 Hz/s^2/m Hz/s^2/m^2 Hz/s^2/m^3' + '\n')
        f.write('receiver_gain:               ' + '{:8.4f}'.format(
            self.receiver_gain) + '   dB' + '\n')
        f.write('calibration_gain:            ' + '{:8.4f}'.format(
            self.calibration_gain) + '   dB' + '\n')
        f.write('sar_to_earth_center:            ' + '{:13.4f}'.format(
            self.sar_to_earth_center) + '   m' + '\n')
        f.write('earth_radius_below_sensor:      ' + '{:13.4f}'.format(
            self.earth_radius_below_sensor) + '   m' + '\n')
        f.write('earth_semi_major_axis:          ' + '{:13.4f}'.format(
            self.earth_semi_major_axis) + '   m' + '\n')
        f.write('earth_semi_minor_axis:          ' + '{:13.4f}'.format(
            self.earth_semi_minor_axis) + '   m' + '\n')
        f.write('number_of_state_vectors:                    ' + str(
            self.number_of_state_vectors) + '\n')
        f.write('time_of_first_state_vector:   ' + '{:15.6f}'.format(
            self.time_of_first_state_vector) + '   s' + '\n')
        f.write('state_vector_interval:        ' + '{:15.6f}'.format(
            self.state_vector_interval) + '   s' + '\n')

        for i in range(0, self.number_of_state_vectors):
            f.write('state_vector_position_' + str(i + 1) + ':' + \
                    '{:16.4f}'.format(self.state_vector_position[i, 0]) + \
                    '{:16.4f}'.format(self.state_vector_position[i, 1]) + \
                    '{:16.4f}'.format(self.state_vector_position[i, 2]) + \
                    '   m   m   m' + '\n')
            f.write('state_vector_velocity_' + str(i + 1) + ':' + \
                    '{:16.5f}'.format(self.state_vector_velocity[i, 0]) + \
                    '{:16.5f}'.format(self.state_vector_velocity[i, 1]) + \
                    '{:16.5f}'.format(self.state_vector_velocity[i, 2]) + \
                    '   m/s m/s m/s' + '\n')
        f.write("\n")

        f.close()


# }}}
class diff_param:  # {{{

    def __init__(self):
        self.r0 = 0
        self.z0 = 0
        self.npix1 = 0
        self.nrec1 = 0
        self.XNO0_1ST1 = 0
        self.N_X01 = 0
        self.rgsp1 = 0.
        self.azsp1 = 0.
        self.npix2 = 0
        self.nrec2 = 0
        self.XNO0_1ST2 = 0
        self.N_X02 = 0.
        self.rgsp2 = 0.
        self.azsp2 = 0.
        self.x_start = 0
        self.x_end = 0
        self.xs = 0
        self.xsp = 0
        self.y_start = 0
        self.y_end = 0
        self.nrec = 0
        self.azsp = 0
        self.ofw_w = 0
        self.ofw_h = 0
        self.ofw_thr = 0.
        self.xoff = np.zeros(6, np.float64)
        self.yoff = np.zeros(6, np.float64)
        self.y_startl = 0
        self.m_yl = 0
        self.m_xl = 0
        self.m_x0 = 0
        self.m_nx = 0
        self.xnlook = 0
        self.ynlook = 0
        self.rgsp_i = np.zeros(6, np.float64)

    def load(self, file):
        self.r0 = np.int32(read_keyword(file, 'initial_range_offset'))
        self.z0 = np.int32(read_keyword(file, 'initial_azimuth_offset'))
        self.npix1 = np.int32(read_keyword(file, 'range_samp_1'))
        self.nrec1 = np.int32(read_keyword(file, 'az_samp_1'))
        self.XNO0_1ST1 = np.int32(
            read_keyword(file, 'first_nonzero_range_pixel_1'))
        self.N_X01 = np.int32(
            read_keyword(file, 'number_of_nonzero_range_pixels_1'))
        self.rgsp1 = np.float64(read_keyword(file, 'range_pixel_spacing_1'))
        self.azsp1 = np.float64(read_keyword(file, 'az_pixel_spacing_1'))
        self.npix2 = np.int32(read_keyword(file, 'range_samp_2'))
        self.nrec2 = np.int32(read_keyword(file, 'az_samp_2'))
        self.XNO0_1ST2 = np.int32(
            read_keyword(file, 'first_nonzero_range_pixel_2'))
        self.N_X02 = np.int32(
            read_keyword(file, 'number_of_nonzero_range_pixels_2'))
        self.rgsp2 = np.float64(read_keyword(file, 'range_pixel_spacing_2'))
        self.azsp2 = np.float64(read_keyword(file, 'az_pixel_spacing_2'))
        self.x_start = np.int32(
            read_keyword(file, 'offset_estimation_starting_range'))
        self.x_end = np.int32(
            read_keyword(file, 'offset_estimation_ending_range'))
        self.xs = np.int32(
            read_keyword(file, 'offset_estimation_range_samples'))
        self.xsp = np.int32(
            read_keyword(file, 'offset_estimation_range_spacing'))
        self.y_start = np.int32(
            read_keyword(file, 'offset_estimation_starting_azimuth'))
        self.y_end = np.int32(
            read_keyword(file, 'offset_estimation_ending_azimuth'))
        self.nrec = np.int32(
            read_keyword(file, 'offset_estimation_azimuth_samples'))
        self.azsp = np.int32(
            read_keyword(file, 'offset_estimation_azimuth_spacing'))
        self.ofw_w = np.int32(
            read_keyword(file, 'offset_estimation_patch_width'))
        self.ofw_h = np.int32(
            read_keyword(file, 'offset_estimation_patch_height'))
        self.ofw_thr = np.float64(
            read_keyword(file, 'offset_estimation_threshold'))
        self.xoff = np.float64(read_keyword(file, 'range_offset_polynomial',
                                            multi_val=[' ', '0', '1', '2', '3',
                                                       '4', '5']))
        self.yoff = np.float64(read_keyword(file, 'azimuth_offset_polynomial',
                                            multi_val=[' ', '0', '1', '2', '3',
                                                       '4', '5']))
        self.y_startl = np.int32(read_keyword(file, 'starting_azimuth_line'))
        self.m_yl = np.int32(read_keyword(file, 'map_azimuth_lines'))
        self.m_xl = np.int32(read_keyword(file, 'map_width'))
        self.m_x0 = np.int32(read_keyword(file, 'first_map_range_pixel'))
        self.m_nx = np.int32(read_keyword(file, 'number_map_range_pixels'))
        self.xnlook = np.int32(read_keyword(file, 'range_looks'))
        self.ynlook = np.int32(read_keyword(file, 'azimuth_looks'))
        self.rgsp_i = np.float64(read_keyword(file, 'diff_phase_fit',
                                              multi_val=[' ', '0', '1', '2',
                                                         '3', '4', '5']))

    def write(self, file):
        f = open(file, 'w')
        f.write('Gamma DIFF&GEO Processing Parameters\n')
        f.write(
            'title: DIFF_par determined from DIFF/GEO DEM parameter files\n')
        f.write('initial_range_offset:                 ' + '{:d}'.format(
            self.r0) + '\n')
        f.write('initial_azimuth_offset:               ' + '{:d}'.format(
            self.z0) + '\n')
        f.write('range_samp_1:                      ' + '{:d}'.format(
            self.npix1) + '\n')
        f.write('az_samp_1:                         ' + '{:d}'.format(
            self.nrec1) + '\n')
        f.write('first_nonzero_range_pixel_1:          ' + '{:d}'.format(
            self.XNO0_1ST1) + '\n')
        f.write('number_of_nonzero_range_pixels_1:     ' + '{:d}'.format(
            self.N_X01) + '\n')
        f.write('range_pixel_spacing_1:         ' + '{:14.6e}'.format(
            self.rgsp1) + '\n')
        f.write('az_pixel_spacing_1:            ' + '{:14.6e}'.format(
            self.azsp1) + '\n')
        f.write('range_samp_2:                       ' + str(self.npix2) + '\n')
        f.write('az_samp_2:                          ' + str(self.nrec2) + '\n')
        f.write('first_nonzero_range_pixel_2:          ' + str(
            self.XNO0_1ST2) + '\n')
        f.write('number_of_nonzero_range_pixels_2:   ' + str(self.N_X02) + '\n')
        f.write('range_pixel_spacing_2:         ' + '{:14.6e}'.format(
            self.rgsp2) + '\n')
        f.write('az_pixel_spacing_2:            ' + '{:14.6e}'.format(
            self.azsp2) + '\n')
        f.write(
            'offset_estimation_starting_range:     ' + str(self.x_start) + '\n')
        f.write(
            'offset_estimation_ending_range:       ' + str(self.x_end) + '\n')
        f.write('offset_estimation_range_samples:      ' + str(self.xs) + '\n')
        f.write('offset_estimation_range_spacing:      ' + str(self.xsp) + '\n')
        f.write(
            'offset_estimation_starting_azimuth:   ' + str(self.y_start) + '\n')
        f.write(
            'offset_estimation_ending_azimuth:     ' + str(self.y_end) + '\n')
        f.write(
            'offset_estimation_azimuth_samples:    ' + str(self.nrec) + '\n')
        f.write(
            'offset_estimation_azimuth_spacing:    ' + str(self.azsp) + '\n')
        f.write(
            'offset_estimation_patch_width:        ' + str(self.ofw_w) + '\n')
        f.write(
            'offset_estimation_patch_height:       ' + str(self.ofw_h) + '\n')
        f.write(
            'offset_estimation_threshold:          ' + str(self.ofw_thr) + '\n')
        f.write('range_offset_polynomial:          ' + \
                '{:14.5e}'.format(self.xoff[0]) + \
                '{:14.5e}'.format(self.xoff[1]) + \
                '{:14.5e}'.format(self.xoff[2]) + \
                '{:14.5e}'.format(self.xoff[3]) + \
                '{:14.5e}'.format(self.xoff[4]) + \
                '{:14.5e}'.format(self.xoff[5]) + '\n')
        f.write('azimuth_offset_polynomial:        ' + \
                '{:14.5e}'.format(self.yoff[0]) + \
                '{:14.5e}'.format(self.yoff[1]) + \
                '{:14.5e}'.format(self.yoff[2]) + \
                '{:14.5e}'.format(self.yoff[3]) + \
                '{:14.5e}'.format(self.yoff[4]) + \
                '{:14.5e}'.format(self.yoff[5]) + '\n')
        f.write('starting_azimuth_line:                ' + str(
            self.y_startl) + '\n')
        f.write(
            'map_azimuth_lines:                    ' + str(self.m_yl) + '\n')
        f.write(
            'map_width:                            ' + str(self.m_xl) + '\n')
        f.write(
            'first_map_range_pixel:                ' + str(self.m_x0) + '\n')
        f.write(
            'number_map_range_pixels:              ' + str(self.m_nx) + '\n')
        f.write(
            'range_looks:                          ' + str(self.xnlook) + '\n')
        f.write(
            'azimuth_looks:                        ' + str(self.ynlook) + '\n')
        f.write('diff_phase_fit:      ' + \
                '{:14.5e}'.format(self.rgsp_i[0]) + \
                '{:14.5e}'.format(self.rgsp_i[1]) + \
                '{:14.5e}'.format(self.rgsp_i[2]) + \
                '{:14.5e}'.format(self.rgsp_i[3]) + \
                '{:14.5e}'.format(self.rgsp_i[4]) + \
                '{:14.5e}'.format(self.rgsp_i[5]) + '\n')

        f.close()


# }}}
class off_param:  # {{{

    def __init__(self):
        self.r0 = 0
        self.z0 = 0
        self.sr0 = 0
        self.snpix = 0
        self.x_start = 0
        self.x_end = 0
        self.npix = 0
        self.rgsp = 0
        self.y_start = 0
        self.y_end = 0
        self.nrec = 0
        self.azsp = 0
        self.ofw_w = 0
        self.ofw_h = 0
        self.ofw_thr = 0
        self.xoff = [0, 0, 0]  # np.zeros(3,np.float64)
        self.yoff = [0, 0, 0]  # np.zeros(3,np.float64)

        self.slc1 = 0
        self.nrec_i = 0
        self.npix_i = 0
        self.xno0_1st = 0
        self.n_x0 = 0
        self.xnlook = 0
        self.ynlook = 0
        self.rgsp_i = 0.
        self.azsp_i = 0.

    def load(self, file):
        self.r0 = np.int32(read_keyword(file, 'initial_range_offset'))
        self.z0 = np.int32(read_keyword(file, 'initial_azimuth_offset'))
        self.sr0 = np.int32(read_keyword(file, 'slc1_starting_range_pixel'))
        self.snpix = np.int32(read_keyword(file, 'number_of_slc_range_pixels'))
        self.x_start = np.int32(
            read_keyword(file, 'offset_estimation_starting_range'))
        self.x_end = np.int32(
            read_keyword(file, 'offset_estimation_ending_range'))
        self.npix = np.int32(
            read_keyword(file, 'offset_estimation_range_samples'))
        self.rgsp = np.int32(
            read_keyword(file, 'offset_estimation_range_spacing'))
        self.y_start = np.int32(
            read_keyword(file, 'offset_estimation_starting_azimuth'))
        self.y_end = np.int32(
            read_keyword(file, 'offset_estimation_ending_azimuth'))
        self.nrec = np.int32(
            read_keyword(file, 'offset_estimation_azimuth_samples'))
        self.azsp = np.int32(
            read_keyword(file, 'offset_estimation_azimuth_spacing'))
        self.ofw_w = np.int32(
            read_keyword(file, 'offset_estimation_window_width'))
        self.ofw_h = np.int32(
            read_keyword(file, 'offset_estimation_window_height'))
        try:  # modification by SJ at 06/20/2019 to deal with offset parameter file from GAMMA when processing S1 data
            self.ofw_thr = np.int32(
                read_keyword(file, 'offset_estimation_threshhold'))
        except:
            self.ofw_thr = np.float32(
                read_keyword(file, 'offset_estimation_threshhold'))
        self.xoff = np.float64(read_keyword(file, 'range_offset_polynomial',
                                            multi_val=[' ', '0', '1', '2']))
        self.yoff = np.float64(read_keyword(file, 'azimuth_offset_polynomial',
                                            multi_val=[' ', '0', '1', '2']))

        self.slc1 = np.int32(read_keyword(file, 'slc1_starting_azimuth_line'))
        self.nrec_i = np.int32(
            read_keyword(file, 'interferogram_azimuth_lines'))
        self.npix_i = np.int32(read_keyword(file, 'interferogram_width'))
        self.xno0_1st = np.int32(
            read_keyword(file, 'first_nonzero_range_pixel'))
        self.n_x0 = np.int32(
            read_keyword(file, 'number_of_nonzero_range_pixels'))
        self.xnlook = np.int32(read_keyword(file, 'interferogram_range_looks'))
        self.ynlook = np.int32(
            read_keyword(file, 'interferogram_azimuth_looks'))
        self.rgsp_i = np.float64(
            read_keyword(file, 'interferogram_range_pixel_spacing',
                         rm_unit='m'))
        self.azsp_i = np.float64(
            read_keyword(file, 'interferogram_azimuth_pixel_spacing',
                         rm_unit='m'))

    def write(self, file):

        f = open(file, 'w')
        f.write('Gamma Interferometric SAR Processor (ISP)\n')
        f.write('Interferogram and Image Offset Parameter File\n')
        f.write('\n')
        f.write('title:     interferogram parameters\n')
        f.write('initial_range_offset:                 ' + str(self.r0) + '\n')
        f.write('initial_azimuth_offset:               ' + str(self.z0) + '\n')
        f.write('slc1_starting_range_pixel:            ' + str(self.sr0) + '\n')
        f.write(
            'number_of_slc_range_pixels:           ' + str(self.snpix) + '\n')
        f.write(
            'offset_estimation_starting_range:     ' + str(self.x_start) + '\n')
        f.write(
            'offset_estimation_ending_range:       ' + str(self.x_end) + '\n')
        f.write(
            'offset_estimation_range_samples:      ' + str(self.npix) + '\n')
        f.write(
            'offset_estimation_range_spacing:      ' + str(self.rgsp) + '\n')
        f.write(
            'offset_estimation_starting_azimuth:   ' + str(self.y_start) + '\n')
        f.write(
            'offset_estimation_ending_azimuth:     ' + str(self.y_end) + '\n')
        f.write(
            'offset_estimation_azimuth_samples:    ' + str(self.nrec) + '\n')
        f.write(
            'offset_estimation_azimuth_spacing:    ' + str(self.azsp) + '\n')
        f.write(
            'offset_estimation_window_width:       ' + str(self.ofw_w) + '\n')
        f.write(
            'offset_estimation_window_height:      ' + str(self.ofw_h) + '\n')
        f.write(
            'offset_estimation_threshhold:         ' + str(self.ofw_thr) + '\n')
        f.write('range_offset_polynomial:     ' + \
                '{:14.5e}'.format(self.xoff[0]) + \
                '{:14.5e}'.format(self.xoff[1]) + \
                '{:14.5e}'.format(self.xoff[2]) + \
                '\n')
        f.write('azimuth_offset_polynomial:   ' + \
                '{:14.5e}'.format(self.yoff[0]) + \
                '{:14.5e}'.format(self.yoff[1]) + \
                '{:14.5e}'.format(self.yoff[2]) + \
                '\n')
        f.write('slc1_starting_azimuth_line:               ' + str(
            self.slc1) + '\n')
        f.write('interferogram_azimuth_lines:              ' + str(
            self.nrec_i) + '\n')
        f.write('interferogram_width:                      ' + str(
            self.npix_i) + '\n')
        f.write('first_nonzero_range_pixel:                ' + str(
            self.xno0_1st) + '\n')
        f.write('number_of_nonzero_range_pixels:           ' + str(
            self.n_x0) + '\n')
        f.write('interferogram_range_looks:                ' + str(
            self.xnlook) + '\n')
        f.write('interferogram_azimuth_looks:              ' + str(
            self.ynlook) + '\n')
        f.write('interferogram_range_pixel_spacing:       ' + str(
            self.rgsp_i) + '\n')
        f.write('interferogram_azimuth_pixel_spacing:     ' + str(
            self.azsp_i) + '\n')
        f.write('resampled_range_pixel_spacing:           0.000000   m' + '\n')
        f.write('resampled_azimuth_pixel_spacing:         0.000000   m' + '\n')
        f.write('resampled_starting_ground_range:         0.000000   m' + '\n')
        f.write('resampled_pixels_per_line:               0' + '\n')
        f.write('resampled_number_of_lines:               0' + '\n')
        f.write('' + '\n')
        f.write(
            '*************** END OF ISP-OFFSET PARAMETERS ******************' + '\n')

        f.close()

# }}}
