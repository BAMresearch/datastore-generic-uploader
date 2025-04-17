#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author:      "Bastian Ruehle"
# @copyright:   "Copyright 2024, Bastian Ruehle, Federal Institute for Materials Research and Testing (BAM)"
# @version:     "1.0.0"
# @maintainer:  "Bastian Ruehle"
# @email        "bastian.ruehle@bam.de"

from typing import Union, Tuple, List, Dict, Optional
import os.path
import json
from datetime import datetime
import numpy as np

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt


def parse_ir(files: Union[list, tuple], create_preview: bool = True) -> dict[str, Union[str, float, int]]:
    """
    Parse ASCII files exported from IR measurements.

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

    filename_spa = ''
    filename_csv = ''
    for i in files:
        if i.lower().endswith('.spa'):
            filename_spa = i
        elif i.lower().endswith('.csv'):
            filename_csv = i

    if filename_spa == '':
        return {}

    metadata: dict[str, Union[str, float, int]] = {}

    fc = [i for i in open(filename_spa, 'rb')]
    for i, l in enumerate(fc):
        if b'Background gemessen am ' in l:
            metadata['START_DATE'] = datetime.strftime(datetime.strptime(fc[i][fc[i].find(b' am  ')+8:fc[i].find(b' (GMT')].decode(), '%b %d %H:%M:%S %Y'), '%Y-%m-%d %H:%M:%S')
            tmp = fc[i+2][fc[i+2].find(b':\t ')+3:fc[i+2].find(b'\r\n')].decode().replace(',', '.').split(' ')
            metadata['FTIR.RESOLUTION'] = int(float(tmp[0]))
            metadata['FTIR.START_WAVENUMBER'] = float(tmp[2])
            metadata['FTIR.END_WAVENUMBER'] = float(tmp[4])
            metadata['FTIR.INSTRUMENT'] = fc[i+3][fc[i+3].find(b': ')+2:fc[i+3].find(b'\r\n')].decode()
            metadata['FTIR.ACCESSORY'] = 'FTIR_ACCESSORY_GOLDEN_GATE'

    if filename_csv != '' and create_preview:
        data = np.array([i.replace(',', '.').replace('\r', '').replace('\n', '').split(';') for i in open(filename_csv)], dtype='float32')
        plt.plot(data[:, 0], data[:, 1])
        plt.xlim((min(4000, float(metadata['FTIR.END_WAVENUMBER'])) + 100, max(550, float(metadata['FTIR.START_WAVENUMBER']))))
        ydata = data[data[:, 0] > 550, 1]
        plt.ylim(np.min(ydata) - 0.05 * abs(np.min(ydata)), np.max(ydata) + 0.05 * abs(np.max(ydata)))
        plt.xlabel('Wavenumber [1/cm]')
        plt.ylabel('Abs [a.u.]')
        plt.tight_layout()
        plt.savefig(f'{os.path.splitext(filename_csv)[0]}_preview.png')

    return metadata
