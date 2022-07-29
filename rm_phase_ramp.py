#!/usr/bin/env python
u"""
Enrico Ciraci' - 03/2022

TEST:
Estimate and Remove the contribution of a "Linear Ramp" to the Wrapped Phase
of a Differential InSAR Interferogram.

usage: rm_phase_ramp.py [-h] [--par PAR] in_interf

positional arguments:
  in_interf          Input Interferogram - Absolute Path

optional arguments:
  -h, --help         show this help message and exit
  --par PAR, -P PAR  Interferogram Parameter File

NOTE: In this implementation of the algorithm, a first guess or preliminary
    estimate of the parameters defining the ramp must be provided by the user.
    These parameters include the number of phase cycles characterizing the ramp
    in the X and Y (columns and rows) directions of the input raster.

A GRID SEARCH around the user-defined first guess is performed to obtain the
best estimate of the ramp parameters.

PYTHON DEPENDENCIES:
    argparse: Parser for command-line options, arguments and sub-commands
           https://docs.python.org/3/library/argparse.html
    numpy: The fundamental package for scientific computing with Python
          https://numpy.org/
    matplotlib: Visualization with Python
        https://matplotlib.org/
    tqdm: Progress Bar in Python.
          https://tqdm.github.io/
    datetime: Basic date and time types
           https://docs.python.org/3/library/datetime.html#module-datetime

    py_gamma: GAMMA's Python integration with the py_gamma module

UPDATE HISTORY:
07/2022: estimate_phase_ramp() - Updated - Accepts ramp parameters as floats.
"""
# - Python dependencies
from __future__ import print_function
import os
import argparse
import datetime
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
from pathlib import Path
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg
from utils.read_keyword import read_keyword
from utils.make_dir import make_dir


def estimate_phase_ramp(dd_phase_complex: np.ndarray, cycle_r: float,
                        cycle_c: float, slope_r: float = 1., slope_c: float = 1.,
                        s_radius: float = 2, s_step: float = 0.1) -> dict:
    """
    Estimate a phase ramp from the provided input interferogram
    :param dd_phase_complex: interferogram phase expressed as complex array
    :param cycle_r: phase ramp number of cycles along rows
    :param cycle_c: phase ramp number of cycles along columns
    :param slope_r: phase ramp slope sign - rows axis
    :param slope_c: phase ramp slope sign - columns axis
    :param s_radius: grid search domain radius
    :param s_step: grid search step
    :return: Python dictionary containing the results of the grid search
    """
    # - Generate synthetic field domain
    array_dim = dd_phase_complex.shape
    n_rows = array_dim[0]
    n_columns = array_dim[1]
    raster_mask = np.ones(array_dim)
    raster_mask[np.isnan(dd_phase_complex)] = 0
    # - Integration Domain used to define the phase ramp
    xx_m, yy_m = np.meshgrid(np.arange(n_columns), np.arange(n_rows))

    if s_radius > 0:
        if cycle_r - s_radius <= 0:
            n_cycle_r_vect_f = np.arange(s_step, cycle_r + s_radius + s_step,
                                         s_step)
        else:
            n_cycle_r_vect_f = np.arange(cycle_r - s_radius,
                                         cycle_r + s_radius + s_step,
                                         s_step)
        if cycle_c - s_radius <= 0:
            n_cycle_c_vect_f = np.arange(s_step, cycle_c + s_radius + s_step,
                                         s_step)
        else:
            n_cycle_c_vect_f = np.arange(cycle_c - s_radius,
                                         cycle_c + s_radius + s_step,
                                         s_step)
        # - Create Grid Search Domain
        error_array_f = np.zeros([len(n_cycle_r_vect_f), len(n_cycle_c_vect_f)])

        for r_count, n_cycle_r in tqdm(enumerate(list(n_cycle_r_vect_f)),
                                       total=len(n_cycle_r_vect_f), ncols=60):
            for c_count, n_cycle_c in enumerate(list(n_cycle_c_vect_f)):
                synth_real = slope_c * (2 * np.pi / n_columns) * n_cycle_c * xx_m
                synth_imag = slope_r * (2 * np.pi / n_rows) * n_cycle_r * yy_m
                synth_phase_plane = synth_real + synth_imag
                synth_complex = np.exp(1j * synth_phase_plane)

                # - Compute Complex Conjugate product between the synthetic
                # - phase ramp and the input interferogram.
                dd_phase_complex_corrected \
                    = np.angle(dd_phase_complex * np.conj(synth_complex))
                # - Compute the Mean Absolute value of the phase residuals
                # - > Mean Absolute Error
                error = np.abs(dd_phase_complex_corrected)
                mae = np.nansum(error) / np.nansum(raster_mask)
                error_array_f[r_count, c_count] = mae

        # - Find location of the Minimum Absolute Error Value
        ind_min = np.where(error_array_f == np.nanmin(error_array_f))
        n_cycle_c = n_cycle_c_vect_f[ind_min[1]][0]
        n_cycle_r = n_cycle_r_vect_f[ind_min[0]][0]
        freq_r = n_cycle_r/n_rows
        freq_c = n_cycle_c/n_columns

    else:
        # - Integration Domain used to define the phase ramp
        freq_r = cycle_r/n_rows
        freq_c = cycle_c/n_columns

    return{'freq_r': freq_r, 'freq_c': freq_c,
           'xx_m': xx_m, 'yy_m': yy_m}


def main() -> None:
    # - Read the system arguments listed after the program
    parser = argparse.ArgumentParser(
        description="""
        """
    )
    # - Positional Arguments
    parser.add_argument('in_interf', type=str, default=None,
                        help='Input Interferogram - Absolute Path')
    # - Interferogram Parameter File
    parser.add_argument('--par', '-P', type=str,
                        help='Interferogram Parameter File',
                        default='DEM_gc_par')

    # - Interferogram Coherence Maps
    parser.add_argument('--coh', '--C', type=str, default=None,
                        help='Coherence Map - Absolute Path', required=True)

    # - Interferogram Coherence Maps
    parser.add_argument('--pwr', '--W', type=str, default=None,
                        help='Reference SLCs intensity image.', required=True)
    args = parser.parse_args()
    # - Output figures parameters
    fig_format = 'jpeg'
    # - Absolute Path to input interferogram
    interf_input_path = Path(args.in_interf)
    # - Extract Data Directory from input file path
    data_dir = interf_input_path.parent
    # - Create Output Directory
    out_dir = make_dir(data_dir.__str__(), 'DERAMP')
    # -
    interf_output_path = Path(os.path.join(data_dir, interf_input_path.name
                                           + '_deramped'))
    # - Interferogram Coherence Mask calculated using pg.edf filter
    coh_mask = Path(args.coh)

    # - Interferogram Parameter File
    par_file = os.path.join(data_dir, args.par)
    # - Interferogram Width
    interf_width = int(read_keyword(par_file, 'width'))

    # - Import Coherence Mask saved as Gamma Software binary image
    # - Note: Set type = float
    coh_in = pg.read_image(coh_mask, width=interf_width, dtype='float')

    # - Show Coherence Mask
    plt.figure()
    plt.title('Interferogram Coherence')
    plt.imshow(coh_in, cmap=plt.get_cmap('viridis'))
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'coherence_map.'+fig_format),
                dpi=200, format=fig_format)
    plt.close()

    # - Compute Binary Mask using grid point with Coherence > 0
    coh_mask = np.zeros(coh_in.shape)
    coh_mask[coh_in > 0.] = 1
    # - Show Binary Mask
    plt.figure()
    plt.title('Binary Mask')
    plt.imshow(coh_mask, cmap=plt.get_cmap('gray'))
    plt.colorbar()
    plt.savefig(os.path.join(out_dir, 'binary_mask.'+fig_format),
                dpi=200, format=fig_format)
    plt.close()

    # - Read Complex Interferogram saved as Gamma Software binary image
    # - Note: Set type = fcomplex
    interf_in = pg.read_image(interf_input_path, width=interf_width,
                              dtype='fcomplex')
    # - Interferogram Size
    n_rows = interf_in.shape[0]
    n_columns = interf_in.shape[1]

    # - Compute wrapped interferometric phase
    data_in_r_phase = np.angle(interf_in)
    plt.figure()
    plt.title('Input Interferometric Phase')
    plt.imshow(data_in_r_phase, cmap=plt.cm.get_cmap('jet'))
    plt.colorbar()
    plt.savefig(os.path.join(out_dir, 'input_interferometric_phase.'+fig_format),
                dpi=200, format=fig_format)
    plt.close()
    print('# - input_interferometric_phase.'+fig_format
          + ' - available inside DERAMP directory.')

    # - Crop the interferogram over the area where the ramp is more easily
    # - detectable.
    print('\n\n# - Chose Interferogram sub region that will be used to'
          'estimate the linear ramp: ')
    row_min = int(input('# - Row Min: '))
    row_max = int(input('# - Row Max: '))
    col_min = int(input('# - Column Min: '))
    col_max = int(input('# - Column Max: '))

    # - Cropped Interferometric Phase Map: region used to estimate the
    # - phase ramp.
    data_in_r_phase_c = data_in_r_phase[row_min: row_max, col_min: col_max]
    plt.figure()
    plt.title('Cropped Interferometric Phase Map')
    plt.imshow(data_in_r_phase_c, cmap=plt.cm.get_cmap('jet'))
    plt.colorbar()
    plt.savefig(os.path.join(out_dir,
                             'cropped_input_interferometric_phase.'+fig_format),
                dpi=200, format=fig_format)
    plt.close()
    print('# - cropped_input_interferometric_phase.'+fig_format
          + ' - available inside DERAMP directory.')

    # - Search Parameters
    print('\n\n# - Phase Ramp Removal Parameters. Provide first guess: ')
    n_cycles_r = float(input('# - Number of Cycles along Rows: '))
    n_cycles_c = float(input('# - Number of Cycles along Columns: '))
    slope_r = float(input('# - Phase Slope along Rows: '))
    slope_c = float(input('# - Phase Slope along Columns: '))
    s_radius = float(input('# - Search Radius - if > 0, use Grid Search: '))

    # - Estimate Phase Ramp Parameters
    print('# - Estimating Phase Ramp Parameters.')
    ramp = estimate_phase_ramp(data_in_r_phase_c, n_cycles_r, n_cycles_c,
                               slope_r=slope_r, slope_c=slope_c,
                               s_radius=s_radius)
    freq_r = ramp['freq_r']
    freq_c = ramp['freq_c']
    xx_m = ramp['xx_m']
    yy_m = ramp['yy_m']

    # - Generate Synthetic Ramp covering the entire interferogram domain.
    synth_real = slope_c * 2 * np.pi * freq_c * xx_m
    synth_imag = slope_r * 2 * np.pi * freq_r * yy_m
    synth_phase_plane = synth_real + synth_imag
    synth_complex = np.exp(1j * synth_phase_plane)
    phase_ramp = np.angle(synth_complex)

    print(' ')
    print('# - Estimated Frequencies: ')
    print(f'# - Fr [cycles/pixel]: {freq_r}')
    print(f'# - Fc [cycles/pixel] : {freq_c}')
    print('# - Total Number of Cycles: ')
    print(f'# - Rows: {freq_r*n_rows}')
    print(f'# - Columns : {freq_c*n_columns}')

    # - Estimated Phase Ramp
    plt.figure()
    plt.title('Estimated Phase Ramp')
    plt.imshow(phase_ramp, cmap=plt.cm.get_cmap('jet'))
    plt.colorbar()
    plt.savefig(os.path.join(out_dir,
                             'phase_ramp.'+fig_format),
                dpi=200, format=fig_format)
    plt.close()

    # - Compute synthetic ramp
    xx_m, yy_m = np.meshgrid(np.arange(n_columns), np.arange(n_rows))
    # - Generate Synthetic Ramp
    synth_real = slope_c * 2 * np.pi * freq_c * xx_m
    synth_imag = slope_r * 2 * np.pi * freq_r * yy_m
    synth_phase_plane = synth_real + synth_imag
    # -  Phase Ramp in Exponential Complex Format
    synth_complex = np.exp(1j * synth_phase_plane)

    # - Remove the estimated phase ramp from the input phase field by
    # - computing the complex conjugate product between the input phase
    # - field and the estimated ramp.
    dd_phase_complex_corrected = interf_in * np.conjugate(synth_complex)
    # - Apply binary mask to the corrected interferogram
    dd_phase_complex_corrected[coh_mask == 0] = 0

    plt.figure()
    plt.title('Deramped Interferogram')
    plt.imshow(np.angle(dd_phase_complex_corrected),
               cmap=plt.cm.get_cmap('jet'))
    plt.colorbar()
    plt.savefig(os.path.join(out_dir,
                             'deramped_interferogram.'+fig_format),
                dpi=200, format=fig_format)
    plt.close()

    # - Save Deramped Interferogram as a Gamma Software binary image
    pg.write_image(dd_phase_complex_corrected, interf_output_path,
                   dtype='fcomplex')

    # - Show Geocoded interferogram
    pg.rasmph_pwr(interf_output_path, Path(args.pwr), interf_width)

    # - Save Geocoded/Deramped Interferogram in GeoTiff format
    out_tiff = Path(os.path.join(data_dir, interf_output_path.name
                                 + '.bmp'))
    ref_raster = Path(os.path.join(data_dir, interf_output_path.name + '..tif'))
    pg.data2geotiff(par_file, out_tiff, 0, ref_raster)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f'# - Computation Time: {end_time - start_time}')
