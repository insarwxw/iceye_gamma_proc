#!/usr/bin/env python
u"""
decimate_state_vect.py
Enrico Ciraci' - 03/2022
Decimate the number of state vectors available inside the considered SLC
parameter file.

usage: decimate_state_vect.py [-h] [--directory DIRECTORY] [--slc SLC]
                              [--rate RATE] [--replace] [--overwrite]

Decimate the number of state vectors available inside the considered
SLC parameter file.

optional arguments:
  -h, --help            show this help message and exit
  --directory DIRECTORY, -D DIRECTORY
                        Project data directory.
  --slc SLC, -S SLC     Considered Single Look Complex.
  --rate RATE, -R RATE  State Vector Decimation Rate.
  --replace             Replace Original Parameter File.
  --overwrite           Overwrite Previously Decimated Parameter File.

PYTHON DEPENDENCIES:
    argparse: Parser for command-line options, arguments and sub-commands
           https://docs.python.org/3/library/argparse.html
    datetime: Basic date and time types
           https://docs.python.org/3/library/datetime.html#module-datetime
    tqdm: Progress Bar in Python.
          https://tqdm.github.io/
    py_gamma: GAMMA's Python integration with the py_gamma module

UPDATE HISTORY:
"""
# - Python dependencies
from __future__ import print_function
import os
import sys
import shutil
import argparse
import datetime
# - GAMMA's Python integration with the py_gamma module
import py_gamma as pg


def main():
    # - Read the system arguments listed after the program
    parser = argparse.ArgumentParser(
        description="""Decimate the number of state vectors available inside
        the considered SLC parameter file.
        """
    )
    # - Working Directory directory.
    default_dir = os.path.join(os.path.expanduser('~'), 'Desktop',
                               'iceye_gamma_test', 'output')
    parser.add_argument('--directory', '-D',
                        type=lambda p: os.path.abspath(
                            os.path.expanduser(p)),
                        default=default_dir,
                        help='Project data directory.')

    parser.add_argument('--slc', '-S',
                        type=str,
                        default=None,
                        help='Considered Single Look Complex.')

    parser.add_argument('--rate', '-R',
                        type=int,
                        default=10,
                        help='State Vector Decimation Rate.')

    parser.add_argument('--replace', action='store_true',
                        help='Replace Original Parameter File.')

    parser.add_argument('--overwrite', action='store_true',
                        help='Overwrite Previously Decimated Parameter File.')

    args = parser.parse_args()

    if args.slc is None:
        print('# - Provide SLC name.')
        sys.exit()

    # - Read SLC par file
    slc_par_path = os.path.join(args.directory, 'slc+par', args.slc+'.par')

    # - Verify if a decimated version of the state vector parameter file
    # - already exists inside the data directory.
    if os.path.isfile(slc_par_path.replace('.par', '.full.par')):
        print('# - Sate vectors already decimated for this file.')
        print(f'# - {slc_par_path}')
        if args.overwrite:
            shutil.copy(slc_par_path.replace('.par', '.full.par'), slc_par_path)
        else:
            print('# - Verify file content.')
            sys.exit()

    slc_par_dict = pg.ParFile(slc_par_path).par_dict
    n_st_vect = int(slc_par_dict['number_of_state_vectors'][0])
    st_vect_interval = slc_par_dict['state_vector_interval'][0]
    st_vect_interval_unit = slc_par_dict['state_vector_interval'][1]
    print(f'# - Number of State Vectors: {n_st_vect}')
    print(f'# - State Vector Interval [{st_vect_interval_unit}]: '
          f'{st_vect_interval}')

    if args.replace:
        # - Replace Original Parameter File
        shutil.copy(slc_par_path, slc_par_path.replace('.par', '.full.par'))
        dec_par_path = slc_par_path
    else:
        # - Save new Parameter file
        dec_par_path = slc_par_path.replace('.par', '.dec.par')

    with open(dec_par_path, 'w', encoding='utf8') as p_fid:
        print('Gamma Interferometric SAR Processor (ISP) '
              '- Image Parameter File\n', file=p_fid)
        for key in slc_par_dict:
            if key == 'number_of_state_vectors':
                n_st_vect_d = int(int(slc_par_dict[key][0])/args.rate)
                print(key + ':' + ' ' * 13 + f'{n_st_vect_d}', file=p_fid)
            elif key == 'state_vector_interval':
                st_vect_int = float(slc_par_dict[key][0])*args.rate
                print(key + ':' + ' ' * 13 + f'{st_vect_int} '
                                             f'{slc_par_dict[key][1]}',
                      file=p_fid)
            elif 'state_vector_position' in key:
                continue
            elif 'state_vector_velocity' in key:
                continue
            else:
                line = ''
                for x in slc_par_dict[key]:
                    line += '  ' + x
                print(key+':' + ' '*13 + line, file=p_fid)

        for st_v in range(1, n_st_vect+1, args.rate):
            if st_v == 1:
                line = f'state_vector_position_{st_v}'
            else:
                line = f'state_vector_position_{int(st_v/args.rate)+1}'
            for x in slc_par_dict[f'state_vector_position_{st_v}']:
                line += '  ' + x
            print(line, file=p_fid)

            if st == 1:
                line = f'state_vector_velocity_{st_v}'
            else:
                line = f'state_vector_velocity_{int(st_v/args.rate)+1}'
            for x in slc_par_dict[f'state_vector_velocity_{st_v}']:
                line += '  ' + x
            print(line, file=p_fid)


# - run main program
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f'# - Computation Time: {end_time - start_time}')
