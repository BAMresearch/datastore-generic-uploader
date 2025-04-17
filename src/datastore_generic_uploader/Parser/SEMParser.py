#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author:      "Bastian Ruehle"
# @copyright:   "Copyright 2024, Bastian Ruehle, Federal Institute for Materials Research and Testing (BAM)"
# @version:     "1.0.0"
# @maintainer:  "Bastian Ruehle"
# @email        "bastian.ruehle@bam.de"

from typing import Union
import os.path
from datetime import datetime
import numpy as np
import math

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar

from PIL import Image


def parse_sem(files: Union[list, tuple], create_preview: bool = True) -> dict[str, Union[str, float, int]]:
    """
    Parse SEM images saved in tif file format.

    Parameters
    ----------
    files: Union[list, tuple]
        The list of files that are being parsed.
    create_preview: bool = True
        If set to True, a preview image called "SEM_preview.png" is created in the same folder as the parsed files. Default is True.

    Returns
    -------
    dict[str, Union[str, float, int]]
        The dictionary with the parsed metadata.
    """


    metadata: dict[str, Union[str, float, int, set]] = {}
    metadata['AcquisitionDateTime'] = ''
    metadata['WorkingDistance'] = set()
    metadata['AccelerationVoltage'] = set()
    metadata['Detector'] = set()
    metadata['PixelSizeX'] = set()
    metadata['PixelSizeY'] = set()
    metadata['ImageSizeX'] = set()
    metadata['ImageSizeY'] = set()

    preview_image_list = {}
    preview_image_list['SEM'] = {}
    preview_image_list['TSEM'] = {}

    def extract_metadata_tif(file_path: str, metadata: dict[str, Union[str, float, int, set]], preview_image_list: dict[str, np.ndarray]) -> tuple[dict[str, Union[str, float, int, set]], dict[str, np.ndarray]]:
        """
        Extract metadata from tif files.

        Parameters
        ----------
        file_path: str
            The path to the parsed file.
        metadata: dict[str, Union[str, float, int, set]]
            The metadata dict that contains the metadata already parsed from other images.
        preview_image_list: dict[str, np.ndarray]
            The preview image dict that contains the preview images already created from other images.

        Returns
        -------
        tuple[dict[str, Union[str, float, int, set]], dict[str, np.ndarray]]
            The updated metadata and preview image dicts.
        """

        # Read the file
        with open(file_path, "rb") as f:
            fc = f.read()

        # Parse tif header
        if fc[0] == 0x49 and fc[1] == 0x49:
            bo = 'little'
        elif fc[0] == 0x4D and fc[1] == 0x4D:
            bo = 'big'
        else:
            exit(-1)

        # Read IFD (only works for baseline tiff with one IFD)
        offset = int.from_bytes(fc[0x04:0x08], byteorder=bo)
        ifd_length = int.from_bytes(fc[offset:offset+2], byteorder=bo)
        ifd = [fc[i:i+12] for i in range(offset+2, ifd_length*12, 12)]
        start_metadata1 = 0
        start_metadata2 = 0
        end_metadata = 0

        for t in ifd:
            if int.from_bytes(t[0:2], byteorder=bo) == 0x0111:  # Tag ID for TIFFTAG_STRIPOFFSETS, i.e., start of image data
                end_metadata = int.from_bytes(t[8:], byteorder=bo)
            elif int.from_bytes(t[0:2], byteorder=bo) == 0x8546:  # Tag ID for first metadata block
                start_metadata1 = int.from_bytes(t[8:], byteorder=bo)
            elif int.from_bytes(t[0:2], byteorder=bo) == 0x8547:  # Tag ID for second metadata block
                start_metadata2 = int.from_bytes(t[8:], byteorder=bo)

        if start_metadata1 == 0 or end_metadata == 0:
            exit(-1)

        # Parse metadata from header and store them in a dictionary
        header = fc[start_metadata1:end_metadata].decode('latin-1')
        header = [i.replace('\r', '') for i in header.split('\n')]
        mode = ''

        for i, t in enumerate(header):
            if t == 'AP_WD':
                metadata['WorkingDistance'].add(header[i+1].replace('WD = ', '').strip())
            elif t == 'AP_PIXEL_SIZE':
                tmp_pixel_size = header[i+1].replace('Pixel Size = ', '').strip()
                metadata['PixelSizeX'].add(tmp_pixel_size)
                metadata['PixelSizeY'].add(tmp_pixel_size)
            elif t == 'DP_DETECTOR_CHANNEL':
                mode = header[i+1].replace('Signal A = ', '').strip()
                metadata['Detector'].add(mode)
            elif t == 'AP_MANUALKV':
                metadata['AccelerationVoltage'].add(header[i+1].replace('EHT Target = ', '').strip())
            elif t == 'AP_DATE':
                date = header[i+1].replace('Date :', '')
                time = '00:00:00'
                for j, s in enumerate(header):
                    if s == 'AP_TIME':
                        time = header[j + 1].replace('Time :', '')
                        break
                metadata['AcquisitionDateTime'] = datetime.strptime(date + ' ' + time, '%d %b %Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')

        # Extract preview image
        if 'SE2' in mode:
            mode = 'TSEM'
        else:
            mode = 'SEM'
        preview_img = np.asarray(Image.open(file_path), dtype='uint8').copy()
        preview_image_list[mode][tmp_pixel_size] = preview_img  # Overwrite previous preview images

        metadata['ImageSizeX'].add(str(preview_img.shape[1]))
        metadata['ImageSizeY'].add(str(preview_img.shape[0]))

        return metadata, preview_image_list

    def write_preview_image(preview_image_list: dict[str, np.ndarray], path: str) -> None:
        """
        Creates a preview image of the data.

        Parameters
        ----------
        preview_image_list: dict[str, np.ndarray]
            The preview image dict that contains the preview images.
        path: str
            The path where the preview image is saved.
        """

        total = len(preview_image_list['SEM']) + len(preview_image_list['TSEM'])

        if total == 0:
            exit(-1)

        cols = math.ceil(math.sqrt(total))
        rows = math.ceil(total/cols)

        img_widths = [preview_image_list['SEM'][i].shape[1] for i in preview_image_list['SEM']]
        img_widths += [preview_image_list['TSEM'][i].shape[1] for i in preview_image_list['TSEM']]

        img_heights = [preview_image_list['SEM'][i].shape[0] for i in preview_image_list['SEM']]
        img_heights += [preview_image_list['TSEM'][i].shape[0] for i in preview_image_list['TSEM']]

        fig = plt.figure(figsize=(4*cols, 4*rows*max(img_heights)/max(img_widths)))
        i = 1

        # SEM Images
        imgs = [(i, preview_image_list['SEM'][i]) for i in preview_image_list['SEM']]
        # imgs.sort(key=lambda t: float(t[0].split(' ')[0]), reverse=True)
        for img in imgs:
            a = fig.add_subplot(rows, cols, i)
            cal = img[0].split(' ')
            img = img[1]
            a.imshow(img, cmap="gray")
            a.axis('off')
            scalebar = ScaleBar(float(cal[0]), cal[1], length_fraction=0.2, location='lower right', dimension='si-length')
            a.add_artist(scalebar)
            i += 1

        # TSEM Images
        imgs = [(i, preview_image_list['TSEM'][i]) for i in preview_image_list['TSEM']]
        # imgs.sort(key=lambda t: float(t[0].split(' ')[0]), reverse=True)
        for img in imgs:
            a = fig.add_subplot(rows, cols, i)
            cal = img[0].split(' ')
            img = img[1]
            a.imshow(img, cmap="gray")
            a.axis('off')
            scalebar = ScaleBar(float(cal[0]), cal[1], length_fraction=0.2, location='lower right', dimension='si-length')
            a.add_artist(scalebar)
            i += 1

        plt.tight_layout()
        plt.savefig(path)

    def get_metadata_for_openbis(metadata: dict[str, Union[str, float, int, set]]) -> dict[str, Union[str, float, int]]:
        """
        Write the extracted metadata to a dictionary that can be used with OpenBIS.

        Parameters
        ----------
        metadata: dict[str, Union[str, float, int, set]]
            The metadata dict that contains the metadata already parsed from other images.

        Returns
        -------
        dict[str, Union[str, float, int]]
            The updated metadata dict.
        """

        PROPERTY_TYPE_CODE_DICT = {
            'WorkingDistance': 'SEM.WORKINGDISTANCE',
            'Detector': 'SEM.DETECTOR',
            'PixelSizeX': 'SEM.PIXELSIZEX',
            'PixelSizeY': 'SEM.PIXELSIZEY',
            'ImageSizeX': 'SEM.IMAGESIZEX',
            'ImageSizeY': 'SEM.IMAGESIZEY',
            'AccelerationVoltage': 'SEM.ACCELERATIONVOLTAGE',
            'AcquisitionDateTime': 'START_DATE',
        }

        md: dict[str, Union[str, float, int]] = {}
        for k in PROPERTY_TYPE_CODE_DICT.keys():
            if k in metadata.keys():
                if isinstance(metadata[k], set):
                    tmp = list(metadata[k])
                    tmp = ';'.join(tmp)
                else:
                    tmp = metadata[k]
                if len(tmp) > 0:
                    md[PROPERTY_TYPE_CODE_DICT[k]] = tmp

        return md

    for file in files:
        if file.endswith('.tif'):
            metadata, preview_image_list = extract_metadata_tif(file, metadata, preview_image_list)

    if len(preview_image_list) > 0 and create_preview:
        write_preview_image(preview_image_list, os.path.join(os.path.dirname(files[0]), 'SEM_preview.png'))

    return get_metadata_for_openbis(metadata)
