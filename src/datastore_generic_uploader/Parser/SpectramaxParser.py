#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author:      "Bastian Ruehle"
# @copyright:   "Copyright 2024, Bastian Ruehle, Federal Institute for Materials Research and Testing (BAM)"
# @version:     "1.0.0"
# @maintainer:  "Bastian Ruehle"
# @email        "bastian.ruehle@bam.de"

from typing import Union
import os.path
import codecs
import numpy as np

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt


def parse_platerader(files: Union[list, tuple], create_preview: bool = True) -> dict[str, Union[str, float, int]]:
    """
    Parse ASCII files exported from Spectramax measurements.

    Parameters
    ----------
    files: Union[list, tuple]
        The list of files that are being parsed.
    create_preview: bool = True
        If set to True, a preview image is created in the same folder as the parsed files. Default is True.

    Returns
    -------
    dict[str, Union[str, float, int]]
        The dictionary with the parsed metadata.
    """

    for file in files:
        if file.endswith('.txt'):
            break
    else:
        return {}

    metadata: dict[str, Union[str, float, int]] = {}

    fc = [i.replace('\r', '').replace('\n', '').split('\t') for i in codecs.open(file, 'r', 'utf-16-le')]
    tmp = 0
    x_data: Union[list[float], list[str], list[list[float]], list[list[str]], list[np.ndarray]] = []
    y_data: Union[list[float], list[list[float]], list[np.ndarray]] = []
    legends = []
    titles = []

    for i, l in enumerate(fc):
        if isinstance(l, list) and len(l) > 0 and l[0] == 'Plate:':
            tmp += 1

            if l[5] == 'Absorbance':
                offset = 0
            elif l[5] == 'Fluorescence':
                offset = 1

            metadata['PLATEREADER.READ_TYPE'] = l[4]  # Endpoint, Spectrum
            metadata['PLATEREADER.READ_MODE'] = l[5]  # Absorbance, Fluorescence, Luminsecence
            metadata['PLATEREADER.NUMBER_OF_WELLS'] = l[18+offset]

            if l[4] == 'Spectrum':
                if l[5] == 'Absorbance':
                    metadata['PLATEREADER.ABSORBANCE_START_WAVELENGTH'] = float(l[11])
                    metadata['PLATEREADER.ABSORBANCE_END_WAVELENGTH'] = float(l[12])
                    metadata['PLATEREADER.ABSORBANCE_RESOLUTION'] = float(l[13])
                    titles.append(f'Absorbance Spectrum\n')
                elif l[5] == 'Fluorescence':
                    metadata['PLATEREADER.SPECTRUM_TYPE'] = l[23]
                    if l[23] == 'Excitation Sweep':
                        metadata['PLATEREADER.EMISSION_WAVELENGTH'] = float(l[24])
                        metadata['PLATEREADER.EXCITATION_START_WAVELENGTH'] = float(l[12])
                        metadata['PLATEREADER.EXCITATION_END_WAVELENGTH'] = float(l[13])
                        metadata['PLATEREADER.EXCITATION_RESOLUTION'] = float(l[14])
                        titles.append(f'Excitation Spectrum\nEm.: {float(l[24])} nm')
                    elif l[23] == 'Emission Sweep':
                        metadata['PLATEREADER.EXCITATION_WAVELENGTH'] = float(l[24])
                        metadata['PLATEREADER.EMISSION_START_WAVELENGTH'] = float(l[12])
                        metadata['PLATEREADER.EMISSION_END_WAVELENGTH'] = float(l[13])
                        metadata['PLATEREADER.EMISSION_RESOLUTION'] = float(l[14])
                        titles.append(f'Emission Spectrum\nEx.: {float(l[24])} nm')
                j = i + 1
                tmp_x = []
                tmp_y = []
                legends.append([fc[j][k] for k in range(2, len(fc[j])) if fc[j+1][k]!=''])
                j += 1
                while fc[j][0] != '':
                    tmp_x.append(float(fc[j][0]))
                    tmp_y.append(np.array([float(k) for k in fc[j][2:] if k !=''], dtype='float32'))
                    j += 1
                x_data.append(np.array(tmp_x))
                y_data.append(np.array(tmp_y))
            elif l[4] == 'Endpoint':
                if l[5] == 'Absorbance':
                    metadata['PLATEREADER.ABSORBANCE_WAVELENGTH'] = float(l[15])
                    titles.append(f'Absorbance Measurement\nAbs.: {float(l[15])} nm')
                elif l[5] == 'Fluorescence':
                    metadata['PLATEREADER.EMISSION_WAVELENGTH'] = float(l[16])
                    metadata['PLATEREADER.EXCITATION_WAVELENGTH'] = float(l[20])
                    titles.append(f'Fluorescence Measurement\nEx.: {float(l[20])} nm, Em.: {float(l[16])} nm')
                j = i + 1
                x_data.append([fc[j][k] for k in range(2, len(fc[j])) if fc[j+1][k] != '' and fc[j+1][k] != '#SAT'])
                j += 1
                y_data.append(np.array([float(k) for k in fc[j][2:] if k != '' and k != '#SAT'], dtype='float32'))
                legends.append([])

    if create_preview:
        cols = 4
        rows = int(round(len(titles)/cols, 0))
        fig = plt.figure(figsize=(4*cols, 3*rows))
        for i in range(0, len(titles)):
            a = fig.add_subplot(rows, cols, i+1)
            if 'Spectrum' in titles[i]:
                for j in range(0, y_data[i].shape[1]):
                    plt.plot(x_data[i], y_data[i][:, j], label=legends[i][j])
                a.legend()
                a.set_xlabel('Wavelength [nm]')
                if titles[i].startswith('Absorbance'):
                    a.set_ylabel('Absorbance')
                else:
                    a.set_ylabel('Intensity [a.u.]')
            else:
                plt.bar(x_data[i], y_data[i])
                a.set_xlabel('Well')
                if titles[i].startswith('Absorbance'):
                    a.set_ylabel('Absorbance')
                else:
                    a.set_ylabel('Intensity [a.u.]')
            a.set_title(titles[i])
        plt.tight_layout()
        plt.savefig(f'{os.path.splitext(file)[0]}_preview.png')

    return metadata
