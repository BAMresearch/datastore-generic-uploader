#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author:      "Bastian Ruehle"
# @copyright:   "Copyright 2024, Bastian Ruehle, Federal Institute for Materials Research and Testing (BAM)"
# @version:     "1.0.0"
# @maintainer:  "Bastian Ruehle"
# @email        "bastian.ruehle@bam.de"

from typing import Union
import os.path
import numpy as np

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt


def parse_dls(files: Union[list, tuple], create_preview: bool = True) -> dict[str, Union[str, float, int]]:
    """
    Parse ASCII files exported from DLS measurements.

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
        if file.endswith('.csv'):
            break
    else:
        return {}

    # Mapping of extracted values to their field names in OpenBIS
    PROPERTY_TYPE_CODE_DICT = {
        # 'Sample Name': '$NAME',
        'Measurement Start Date And Time/Size Measurement Result': 'START_DATE',
        'Name/Material Settings/Material/Sample Settings/Sample Settings/Size Measurement Result': 'DLS.MATERIAL',
        'Name/Dispersant Settings/Dispersant/Sample Settings/Sample Settings/Size Measurement Result': 'DLS.DISPERSANT',
        'Analysis Model/Size Analysis Settings/Size Analysis/Size Measurement Settings/Measurement Settings/Size Measurement Result': 'DLS.ANALYSISMODEL',
        'Cell Name/Cell Description Settings/View Settings/Cell Settings/Cell/Sample Settings/Sample Settings/Size Measurement Result': 'DLS.CELLDESCRIPTION',
        'Description/Cell Description Settings/View Settings/Cell Settings/Cell/Sample Settings/Sample Settings/Size Measurement Result': 'DLS.CELLDESCRIPTION',
        'Fka Model/Zeta Fka Parameter Settings/Zeta F Ka Parameter Settings/Zeta Analysis Settings/Zeta Analysis/Zeta Measurement Settings/Measurement Settings/Zeta Measurement Result': 'DLS.FKAMODEL'
    }

    metadata: dict[str, Union[str, float, int]] = {}
    attenuators: list[float] = []
    temperatures: list[float] = []
    zaverages: list[float] = []
    polydispersities: list[float] = []
    zeta_averages: list[float] = []
    numbers: Union[list[list[float]], np.ndarray] = []
    volumes: Union[list[list[float]], np.ndarray] = []
    intensities: Union[list[list[float]], np.ndarray] = []
    sizes: Union[list[list[float]], np.ndarray] = []
    zetas: Union[list[list[float]], np.ndarray, list[np.ndarray]] = []
    pots: Union[list[list[float]], np.ndarray, list[np.ndarray]] = []
    int_sizes: Union[list[list[float]], list[float], tuple[float, ...]] = []
    int_widths: Union[list[list[float]], list[float], tuple[float, ...]] = []
    int_areas: Union[list[list[float]], list[float], tuple[float, ...]] = []
    vol_sizes: Union[list[list[float]], list[float], tuple[float, ...]] = []
    vol_widths: Union[list[list[float]], list[float], tuple[float, ...]] = []
    vol_areas: Union[list[list[float]], list[float], tuple[float, ...]] = []
    num_sizes: Union[list[list[float]], list[float], tuple[float, ...]] = []
    num_widths: Union[list[list[float]], list[float], tuple[float, ...]] = []
    num_areas: Union[list[list[float]], list[float], tuple[float, ...]] = []
    zeta_potentials: Union[list[list[float]], list[float], tuple[float, ...]] = []
    zeta_widths: Union[list[list[float]], list[float], tuple[float, ...]] = []
    zeta_areas: Union[list[list[float]], list[float], tuple[float, ...]] = []
    intercepts: list[float] = []
    cumulants_errors: list[float] = []
    multimodal_errors: list[float] = []
    conductivities: list[float] = []
    voltages: list[float] = []

    runs = -1
    li = [int_areas, int_sizes, int_widths, vol_areas, vol_sizes, vol_widths, num_areas, num_sizes, num_widths, zeta_areas, zeta_potentials, zeta_widths]

    # Read file content
    fc = [i.replace('\r', '').replace('\n', '').split(';') for i in open(file, 'r', encoding='latin1')]

    # Extract data (averaging in case of multiple entries)
    for i, c in enumerate(fc):
        if c[0] == '':
            continue
        if c[0] in PROPERTY_TYPE_CODE_DICT.keys():
            # Check if it is a String field (those have the full name in the PROPERTY_TYPE_CODE_DICT), and if so, just use the value directly
            if c[0] == 'Measurement Start Date And Time/Size Measurement Result':
                metadata[PROPERTY_TYPE_CODE_DICT[c[0]]] = fc[i][1].replace('T', ' ').replace('Z', '').split('.')[0]
            else:
                metadata[PROPERTY_TYPE_CODE_DICT[c[0]]] = fc[i][1]
        else:
            # If it is a float field, append the results for averaging
            if 'Unclassified ' in c[0]:
                continue

            if c[0].startswith('Sizes [nm] (Run '):
                assert isinstance(sizes, list)
                sizes.append([float(j) for j in c[1:]])
            elif c[0].startswith('Intensity [%] (Run '):
                assert isinstance(intensities, list)
                intensities.append([float(j) for j in c[1:]])
            elif c[0].startswith('Volume [%] (Run '):
                assert isinstance(volumes, list)
                volumes.append([float(j) for j in c[1:]])
            elif c[0].startswith('Number [%] (Run '):
                assert isinstance(numbers, list)
                numbers.append([float(j) for j in c[1:]])
            elif c[0].startswith('Zeta Potential [mV] (Run '):
                assert isinstance(pots, list)
                pots.append([float(j) for j in c[1:]])
            elif c[0].startswith('Counts [kcps] (Run '):
                assert isinstance(zetas, list)
                zetas.append([float(j) for j in c[1:]])
            elif c[0].startswith('Data for '):
                runs += 1
                for j in li:
                    j.append([])
            elif c[0] == 'Attenuator/Actual Instrument Settings/Actual Instrument Settings/Size Measurement Result':
                attenuators.append(float(fc[i][1]))
            elif c[0] == 'Temperature (°C)/Actual Instrument Settings/Actual Instrument Settings/Size Measurement Result':
                temperatures.append(float(fc[i][1]))
            elif c[0] == 'Z-Average (nm)/Cumulants Result/Cumulants Result/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                zaverages.append(float(fc[i][1]))
            elif c[0] == 'Polydispersity Index (PI)/Cumulants Result/Cumulants Result/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                polydispersities.append(float(fc[i][1]))
            elif c[0] == 'Intercept/Cumulants Result/Cumulants Result/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                intercepts.append(float(fc[i][1]))
            elif c[0] == 'Fit Error/Cumulants Result/Cumulants Result/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                cumulants_errors.append(float(fc[i][1]))
            elif c[0] == 'Fit Error/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                multimodal_errors.append(float(fc[i][1]))
            elif c[0] == 'Zeta Potential (mV)/Zeta Analysis Result/Zeta Analysis Result/Zeta Measurement Result':
                zeta_averages.append(float(fc[i][1]))
            elif c[0] == 'Measured Voltage (V)/Zeta Analysis Result/Zeta Analysis Result/Zeta Measurement Result':
                voltages.append(float(fc[i][1]))
            elif c[0] == 'Conductivity (mS/cm)/Zeta Analysis Result/Zeta Analysis Result/Zeta Measurement Result':
                conductivities.append(float(fc[i][1]))
            elif c[0].startswith('Data for '):
                runs += 1
                for j in li:
                    j.append([])
            elif c[0] == 'Mean/Size Peak/Particle Size Intensity Distribution Peaks ordered by area/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                int_sizes[runs].append(float(c[1]))
            elif c[0] == 'Standard Deviation/Size Peak/Particle Size Intensity Distribution Peaks ordered by area/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                int_widths[runs].append(float(c[1]))
            elif c[0] == 'Area/Size Peak/Particle Size Intensity Distribution Peaks ordered by area/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                int_areas[runs].append(float(c[1]))
            elif c[0] == 'Mean/Size Peak/Particle Size Volume Distribution Peaks ordered by area/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                vol_sizes[runs].append(float(c[1]))
            elif c[0] == 'Standard Deviation/Size Peak/Particle Size Volume Distribution Peaks ordered by area/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                vol_widths[runs].append(float(c[1]))
            elif c[0] == 'Area/Size Peak/Particle Size Volume Distribution Peaks ordered by area/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                vol_areas[runs].append(float(c[1]))
            elif c[0] == 'Mean/Size Peak/Particle Size Number Distribution Peaks ordered by area/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                num_sizes[runs].append(float(c[1]))
            elif c[0] == 'Standard Deviation/Size Peak/Particle Size Number Distribution Peaks ordered by area/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                num_widths[runs].append(float(c[1]))
            elif c[0] == 'Area/Size Peak/Particle Size Number Distribution Peaks ordered by area/Size Analysis Result/Size Analysis Result/Size Measurement Result':
                num_areas[runs].append(float(c[1]))
            elif c[0] == 'Mean/Size Peak/Zeta Peaks/Zeta Analysis Result/Zeta Analysis Result/Zeta Measurement Result':
                zeta_potentials[runs].append(float(c[1]))
            elif c[0] == 'Standard Deviation/Size Peak/Zeta Peaks/Zeta Analysis Result/Zeta Analysis Result/Zeta Measurement Result':
                zeta_widths[runs].append(float(c[1]))
            elif c[0] == 'Area/Size Peak/Zeta Peaks/Zeta Analysis Result/Zeta Analysis Result/Zeta Measurement Result':
                zeta_areas[runs].append(float(c[1]))

    # Average peaks across runs
    all_items = [[int_areas, int_sizes, int_widths], [vol_areas, vol_sizes, vol_widths], [num_areas, num_sizes, num_widths], [zeta_areas, zeta_potentials, zeta_widths]]
    # Fill rugged arrays with nans for converting to numpy, then average across runs, ignoring nans and using slice notation [:] to modify in-place
    for li in all_items:
        max_len = max([len(jt) for it in li for jt in it])
        k = 0
        for it in li:
            for jt in it:
                while len(jt) < max_len:
                    jt.append(np.nan)
            it[:] = np.nanmean(it[:], axis=0)

    # Sort peaks by Area
    if len(int_areas) > 0:
        int_areas, int_sizes, int_widths = zip(*sorted(list(zip(int_areas, int_sizes, int_widths)), reverse = True))
    if len(vol_areas) > 0:
        vol_areas, vol_sizes, vol_widths = zip(*sorted(list(zip(vol_areas, vol_sizes, vol_widths)), reverse = True))
    if len(num_areas) > 0:
        num_areas, num_sizes, num_widths = zip(*sorted(list(zip(num_areas, num_sizes, num_widths)), reverse = True))
    if len(zeta_areas) > 0:
        zeta_areas, zeta_potentials, zeta_widths  = zip(*sorted(list(zip(zeta_areas, zeta_potentials, zeta_widths)), reverse = True))

    # Calculate PD for individual Peaks
    int_pis = np.array(int_widths) / np.array(int_sizes)
    vol_pis = np.array(vol_widths) / np.array(vol_sizes)
    num_pis = np.array(num_widths) / np.array(num_sizes)

    # Average the numerical values for certain fields and add them to the metadata dict:
    metadata['DLS.ATTENUATOR'] = int(np.array(attenuators).mean())
    metadata['DLS.TEMPERATURE'] = round(np.array(temperatures).mean(), 2)
    metadata['DLS.ZAVG'] = round(np.array(zaverages).mean(), 2)
    metadata['DLS.PDI'] = round(np.array(polydispersities).mean(), 3)
    metadata['DLS.INTERCEPT'] = round(np.array(intercepts).mean(), 3)
    metadata['DLS.CUMULANTSFITERROR'] = round(np.array(cumulants_errors).mean(), 6)
    metadata['DLS.MULTIMODALFITERROR'] = round(np.array(multimodal_errors).mean(), 6)
    if len(zeta_areas) > 0:
        metadata['DLS.ZETA'] = round(np.array(zeta_averages).mean(), 2)
        metadata['DLS.VOLT'] = round(np.array(voltages).mean(), 2)
        metadata['DLS.COND'] = round(np.array(conductivities).mean(), 4)

    # For the different distribution types, report data for the first three peaks
    for i in range(0, min(3, len(int_sizes))):
        metadata[f'DLS.PK{i + 1}INT'] = round(int_sizes[i], 2)
        metadata[f'DLS.PK{i + 1}INTWIDTH'] = round(int_widths[i], 2)
        metadata[f'DLS.PK{i + 1}INTPD'] = round(int_pis[i], 2)
    for i in range(0, min(3, len(vol_sizes))):
        metadata[f'DLS.PK{i + 1}VOL'] = round(vol_sizes[i], 2)
        metadata[f'DLS.PK{i + 1}VOLWIDTH'] = round(vol_widths[i], 2)
        metadata[f'DLS.PK{i + 1}VOLPD'] = round(vol_pis[i], 2)
    for i in range(0, min(3, len(num_sizes))):
        metadata[f'DLS.PK{i + 1}NUM'] = round(num_sizes[i], 2)
        metadata[f'DLS.PK{i + 1}NUMWIDTH'] = round(num_widths[i], 2)
        metadata[f'DLS.PK{i + 1}NUMPD'] = round(num_pis[i], 2)
    for i in range(0, min(3, len(zeta_potentials))):
        metadata[f'DLS.PK{i + 1}ZETA'] = round(zeta_potentials[i], 2)
        metadata[f'DLS.PK{i + 1}ZETAWIDTH'] = round(zeta_widths[i], 2)

    if create_preview:
        # Sort peaks by Area
        if len(int_areas) > 0:
            int_areas, int_sizes, int_widths = zip(*sorted(list(zip(int_areas, int_sizes, int_widths)), reverse = True))
        if len(vol_areas) > 0:
            vol_areas, vol_sizes, vol_widths = zip(*sorted(list(zip(vol_areas, vol_sizes, vol_widths)), reverse = True))
        if len(num_areas) > 0:
            num_areas, num_sizes, num_widths = zip(*sorted(list(zip(num_areas, num_sizes, num_widths)), reverse = True))
        if len(zeta_areas) > 0:
            zeta_areas, zeta_potentials, zeta_widths = zip(*sorted(list(zip(zeta_areas, zeta_potentials, zeta_widths)), reverse = True))

        # Plot Data
        f = 1
        if len(zetas) > 0:
            rows = 3
            cols = 2
        else:
            rows = 2
            cols = 2
        sizes = np.asarray(sizes)
        numbers = np.asarray(numbers)
        volumes = np.asarray(volumes)
        intensities = np.asarray(intensities)
        zetas = [np.asarray(i) for i in zetas]  # number of entries can vary for zeta potential and numpy does not like ragged arrays
        pots = [np.asarray(i) for i in pots]

        fig = plt.figure(figsize=(12, 9 * rows / cols))
        if intensities.shape[0] > 0:
            a = fig.add_subplot(rows, cols, f)
            plt.xscale('log')
            for i in range(0, sizes.shape[0]):
                plt.plot(sizes[i], intensities[i], label=f'Run {i+1}')
            a.set_xlabel('Size [nm]')
            a.set_ylabel('Intensity [%]')
            res = ";".join([f'{round(int_sizes[i], 1)}+/-{round(int_widths[i], 1)}' for i in range(0, len(int_sizes))])
            a.set_title(f'Size Intensity Distribution:\nPeak Position (Avg) [nm]: {res}')
            a.legend()
            f += 1
        if volumes.shape[0] > 0:
            a = fig.add_subplot(rows, cols, f)
            plt.xscale('log')
            for i in range(0, sizes.shape[0]):
                plt.plot(sizes[i], volumes[i], label=f'Run {i+1}')
            a.set_xlabel('Size [nm]')
            a.set_ylabel('Volume [%]')
            res = ";".join([f'{round(vol_sizes[i], 1)}+/-{round(vol_widths[i], 1)}' for i in range(0, len(vol_sizes))])
            a.set_title(f'Size Volume Distribution:\nPeak Position (Avg) [nm]: {res}')
            a.legend()
            f += 1
        if numbers.shape[0] > 0:
            a = fig.add_subplot(rows, cols, f)
            plt.xscale('log')
            for i in range(0, sizes.shape[0]):
                plt.plot(sizes[i], numbers[i], label=f'Run {i+1}')
            a.set_xlabel('Size [nm]')
            a.set_ylabel('Number [%]')
            res = ";".join([f'{round(num_sizes[i], 1)}+/-{round(num_widths[i], 1)}' for i in range(0, len(num_sizes))])
            a.set_title(f'Size Number Distribution:\nPeak Position (Avg) [nm]: {res}')
            a.legend()
            f += 1

        a = fig.add_subplot(rows, cols, f)
        plt.xscale('log')
        if len(intensities) > 0:
            plt.plot(sizes[0], np.mean(intensities, 0), 'b', label='Intensity')
        if len(volumes) > 0:
            plt.plot(sizes[0], np.mean(volumes, 0), 'g', label='Volume')
        if len(numbers) > 0:
            plt.plot(sizes[0], np.mean(numbers, 0), 'r', label='Number')
        a.set_xlabel('Size [nm]')
        a.set_ylabel('Frequency [%]')
        res = ";".join([f'Run {i+1}: {round(zaverages[i], 1)} ({round(polydispersities[i], 2)})' for i in range(0, len(zaverages))])
        a.set_title(f'Combined Plots: Z-Average (PDI) [nm]:\n{res}')
        a.legend()
        f += 1

        if len(zetas) > 0:
            # zeta_potentials = [pots[i][np.argmax(zetas[i])] for i in range(0, len(pots))]
            a = fig.add_subplot(rows, cols, f)
            for i in range(0, len(zetas)):
                plt.plot(pots[i], zetas[i], label=f'Run {i+1}')
            a.set_xlabel('Zeta Potential [mV]')
            a.set_ylabel('Intensity [kcps]')
            res = ";".join([f'{round(zeta_potentials[i], 1)}+/-{round(zeta_widths[i], 1)}' for i in range(0, len(zeta_potentials))])
            a.set_title(f'Zeta Potential Distribution:\nPeak Position (Avg) [mv]: {res}')
            a.legend()
            f += 1

        plt.tight_layout()
        plt.savefig(f'{os.path.splitext(file)[0]}_preview.png')

    return metadata
