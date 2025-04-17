#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author:      "Bastian Ruehle"
# @copyright:   "Copyright 2024, Bastian Ruehle, Federal Institute for Materials Research and Testing (BAM)"
# @version:     "1.0.0"
# @maintainer:  "Bastian Ruehle"
# @email        "bastian.ruehle@bam.de"

from typing import Union
import os.path
import json
from datetime import datetime
import numpy as np
import math

import xml.etree.ElementTree as ET
import h5py
from PIL import Image

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar

import Parser._dm3_lib_modified as dm3


def parse_tem(files: Union[list, tuple], create_preview: bool = True) -> dict[str, Union[str, float, int]]:
    """
    Parse TEM images saved in dm3, emd, or tif file format

    Parameters
    ----------
    files: Union[list, tuple]
        The list of files that are being parsed.
    create_preview: bool = True
        If set to True, a preview image called "TEM_preview.png" is created in the same folder as the parsed files. Default is True.

    Returns
    -------
    dict[str, Union[str, float, int]]
        The dictionary with the parsed metadata.
    """

    metadata: dict[str, Union[str, float, int, set]] = {}
    metadata['Instrument'] = ''
    metadata['AcquisitionDateTime'] = ''
    metadata['OperatingMode'] = set()
    metadata['ProjectorMode'] = set()
    metadata['AccelerationVoltage'] = set()
    metadata['Detector'] = set()
    metadata['PixelSizeX'] = set()
    metadata['PixelSizeY'] = set()
    metadata['ImageSizeX'] = set()
    metadata['ImageSizeY'] = set()
    metadata['Magnification'] = set()
    metadata['CameraLength'] = set()
    metadata['SA_ApertureDiameter'] = set()
    metadata['SA_AperturePosX'] = set()
    metadata['SA_AperturePosY'] = set()
    metadata['UserID'] = set()
    metadata['SampleID'] = set()
    metadata['SampleDescription'] = set()
    metadata['SpotIndex'] = set()
    metadata['GunLensSetting'] = set()
    metadata['Aperture[C2].Name'] = set()
    metadata['Aperture[OBJ].Name'] = set()

    preview_image_list = {}
    preview_image_list['TEM;Imaging'] = {}
    preview_image_list['TEM;Diffraction'] = {}
    preview_image_list['STEM;Diffraction'] = {}

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

        # xml namespaces
        ns = {'xmlns:nil': 'http://schemas.fei.com/Metadata/v1/2013/07',
              'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

        # Read the file and search for xml metadata
        with open(file_path, "rb") as f:
            fc = f.read()

        fc = fc[fc.rfind(b'<?xml version='):fc.rfind(b'</Metadata>') + len(b'</Metadata>')].decode('utf-8')

        if fc == '':  # no xml data found
            return metadata

        # Parse the metadata and store them in a dictionary
        tree = ET.ElementTree(ET.fromstring(fc))
        root = tree.getroot()

        # metadata['Instrument'] = root.find('Instrument', ns).find('Manufacturer', ns).text
        # metadata['Instrument'] += ' ' + root.find('Instrument', ns).find('InstrumentModel', ns).text
        metadata['Instrument'] = root.find('Instrument', ns).find('InstrumentModel', ns).text
        metadata['AcquisitionDateTime'] = root.find('Acquisition', ns).find('AcquisitionDatetime', ns).text.replace('T', ' ')
        metadata['AcquisitionDateTime'] = metadata['AcquisitionDateTime'][:metadata['AcquisitionDateTime'].rfind('.')]
        tmp_operating_mode = root.find('Optics', ns).find('OperatingMode', ns).text
        metadata['OperatingMode'].add(tmp_operating_mode)
        tmp_projector_mode = root.find('Optics', ns).find('ProjectorMode', ns).text
        metadata['ProjectorMode'].add(tmp_projector_mode)
        metadata['AccelerationVoltage'].add('{} keV'.format(int(root.find('Optics', ns).find('AccelerationVoltage', ns).text)//1000))
        metadata['Detector'].add(root.find('BinaryResult', ns).find('Detector', ns).text)
        metadata['SpotIndex'].add(root.find('Optics', ns).find('SpotIndex', ns).text)
        metadata['GunLensSetting'].add(root.find('Optics', ns).find('GunLensSetting', ns).text)
        if root.find('Core', ns) is not None and root.find('Core', ns).find('UserID', ns) is not None:  # Exported from new software version (contains more fields)
            metadata['UserID'].add(root.find('Core', ns).find('UserID', ns).text)
        if root.find('Sample', ns) is not None and root.find('Sample', ns).find('SampleID', ns) is not None:  # Exported from new software version (contains more fields)
            metadata['SampleID'].add(root.find('Sample', ns).find('SampleID', ns).text)
        if root.find('Sample', ns) is not None and root.find('Sample', ns).find('SampleDescription', ns) is not None:  # Exported from new software version (contains more fields)
            metadata['SampleDescription'].add(root.find('Sample', ns).find('SampleDescription', ns).text)

        tmp_pixel_size_x = root.find('BinaryResult', ns).find('PixelSize', ns).find('X', ns).text
        tmp_pixel_size_x += ' ' + root.find('BinaryResult', ns).find('PixelSize', ns).find('X', ns).get('unit')
        metadata['PixelSizeX'].add(tmp_pixel_size_x)
        tmp_pixel_size_y = root.find('BinaryResult', ns).find('PixelSize', ns).find('Y', ns).text
        tmp_pixel_size_y += ' ' + root.find('BinaryResult', ns).find('PixelSize', ns).find('Y', ns).get('unit')
        metadata['PixelSizeY'].add(tmp_pixel_size_y)

        for p in root.find('CustomPropertyGroup', ns).find('CustomProperties', ns):
            if p.get('name') == 'Aperture[C2].Name':
                metadata['Aperture[C2].Name'].add(p.get('value'))
            if p.get('name') == 'Aperture[OBJ].Name':
                metadata['Aperture[OBJ].Name'].add(p.get('value'))

        if tmp_operating_mode == 'TEM':
            metadata['ImageSizeX'].add(root.find('BinaryResult', ns).find('ImageSize', ns).find('X', ns).text)
            metadata['ImageSizeY'].add(root.find('BinaryResult', ns).find('ImageSize', ns).find('Y', ns).text)
            if tmp_projector_mode == 'Imaging':  # Brightfield
                metadata['Magnification'].add(root.find('Optics', ns).find('NominalMagnification', ns).text)
            else:  # ED
                pass  # Magnification metadata field not present in ED
        else:  # STEM
            metadata['CameraLength'].add(root.find('Optics', ns).find('CameraLength', ns).text)
            metadata['ImageSizeX'].add(root.find('ScanSettings', ns).find('ScanSize', ns).find('Width', ns).text)
            metadata['ImageSizeY'].add(root.find('ScanSettings', ns).find('ScanSize', ns).find('Height', ns).text)
            for p in root.find('CustomPropertyGroup', ns).find('CustomProperties', ns):
                if p.get('name') == 'StemMagnification':
                    metadata['Magnification'].add(p.get('value'))
                    break

        # These xml fields are always present, but they are not really importrant for the other modes
        if tmp_projector_mode == 'Diffraction':
            for i in root.iter('Aperture'):
                if i.find('Name', ns).text == 'SA':  # Selected Area Aperture
                    if i.find('Type', ns).text == 'None':  # Check if Aperture is actually used
                        break
                    metadata['CameraLength'].add(root.find('Optics', ns).find('CameraLength', ns).text)
                    metadata['SA_ApertureDiameter'].add(i.find('Diameter', ns).text)
                    metadata['SA_AperturePosX'].add(i.find('PositionOffset', ns).find('X', ns).text)
                    metadata['SA_AperturePosY'].add(i.find('PositionOffset', ns).find('Y', ns).text)
                else:
                    continue

        # Extract preview image
        preview_img = np.asarray(Image.open(file_path), dtype='float32').copy()
        preview_image_list['{};{}'.format(tmp_operating_mode, tmp_projector_mode)][tmp_pixel_size_x] = preview_img  # Overwrite previous preview images

        return metadata, preview_image_list

    def extract_metadata_emd(file_path: str, metadata: dict[str, Union[str, float, int, set]], preview_image_list: dict[str, np.ndarray]):
        """
        Extract metadata from emd files.

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
        dict[str, Union[str, float, int, set]], dict[str, np.ndarray]
            The updated metadata and preview image dicts.
        """

        with h5py.File(file_path, 'r') as f:
            # Check if there is an image in the emd file (not the case for edx spectra)
            if f.get('Data/Image') is None:
                return metadata, preview_image_list
            # Take the first image (currently we don't have multiple images per file)
            image_id = [im for im in f.get('Data/Image')][0]

            # Parse imagedata into numpy array
            img = np.squeeze(f.get('Data/Image/{}/Data'.format(image_id)))

            # Parse the metadata from a bytearray into a string
            all_metadata = bytearray(np.squeeze(f.get('Data/Image/{}/Metadata'.format(image_id)))).decode('utf-8').replace('\x00', '')

        if all_metadata == '':  # no json data found
            return metadata

        # Convert to json
        all_metadata = json.loads(all_metadata)

        # metadata['Instrument'] = all_metadata['Instrument']['Manufacturer']
        # metadata['Instrument'] += ' ' + all_metadata['Instrument']['InstrumentModel']
        metadata['Instrument'] = all_metadata['Instrument']['InstrumentModel']
        metadata['AcquisitionDateTime'] = all_metadata['Acquisition']['AcquisitionStartDatetime']['DateTime']
        metadata['AcquisitionDateTime'] = datetime.utcfromtimestamp(int(metadata['AcquisitionDateTime'])).strftime('%Y-%m-%d %H:%M:%S')
        tmp_operating_mode = all_metadata['Optics']['OperatingMode']
        tmp_projector_mode = all_metadata['Optics']['ProjectorMode']
        metadata['AccelerationVoltage'].add('{} keV'.format(int(all_metadata['Optics']['AccelerationVoltage'])//1000))
        metadata['Detector'].add(all_metadata['BinaryResult']['Detector'])
        tmp_pixel_size_x = all_metadata['BinaryResult']['PixelSize']['width']
        tmp_pixel_size_x += ' ' + all_metadata['BinaryResult']['PixelUnitX']
        metadata['PixelSizeX'].add(tmp_pixel_size_x)
        tmp_pixel_size_y = all_metadata['BinaryResult']['PixelSize']['height']
        tmp_pixel_size_y += ' ' + all_metadata['BinaryResult']['PixelUnitY']
        metadata['PixelSizeY'].add(tmp_pixel_size_y)
        metadata['SpotIndex'].add(all_metadata['Optics']['SpotIndex'])
        metadata['GunLensSetting'].add(all_metadata['Optics']['GunLensSetting'])
        metadata['Aperture[C2].Name'].add(all_metadata['CustomProperties']['Aperture[C2].Name']['value'])
        metadata['Aperture[OBJ].Name'].add(all_metadata['CustomProperties']['Aperture[OBJ].Name']['value'])

        if 'Core' in all_metadata and 'UserId' in all_metadata['Core']:  # Exported from new software version (contains more fields)
            metadata['UserID'].add(all_metadata['Core']['UserId'])
        if 'Sample' in all_metadata and 'SampleId' in all_metadata['Sample']:  # Exported from new software version (contains more fields)
            metadata['SampleID'].add(all_metadata['Sample']['SampleId'])
        if 'Sample' in all_metadata and 'SampleDescription' in all_metadata['Sample']:  # Exported from new software version (contains more fields)
            metadata['SampleDescription'].add(all_metadata['Sample']['SampleDescription'])

        if tmp_operating_mode == '1':
            tmp_operating_mode = 'TEM'
            metadata['OperatingMode'].add('TEM')
            metadata['ImageSizeX'].add(all_metadata['BinaryResult']['ImageSize']['width'])
            metadata['ImageSizeY'].add(all_metadata['BinaryResult']['ImageSize']['height'])
        elif tmp_operating_mode == '2':
            tmp_operating_mode = 'STEM'
            metadata['OperatingMode'].add('STEM')
            metadata['ImageSizeX'].add(all_metadata['Scan']['ScanSize']['width'])
            metadata['ImageSizeY'].add(all_metadata['Scan']['ScanSize']['height'])

        if tmp_projector_mode == '1':
            tmp_projector_mode = 'Diffraction'
            metadata['ProjectorMode'].add('Diffraction')
            metadata['CameraLength'].add(all_metadata['Optics']['CameraLength'])
            if tmp_operating_mode == 'STEM':
                metadata['Magnification'].add(all_metadata['CustomProperties']['StemMagnification']['value'])
        elif tmp_projector_mode == '2':
            tmp_projector_mode = 'Imaging'
            metadata['ProjectorMode'].add('Imaging')
            metadata['Magnification'].add(all_metadata['Optics']['NominalMagnification'])

        # These xml fields are always present, but they are not really important for the other modes
        if tmp_projector_mode == 'Diffraction':
            for i in all_metadata['Optics']['Apertures'].keys():
                j = all_metadata['Optics']['Apertures'][i]
                if j['Name'] == 'SA' and j['Type'] != 'None':
                    metadata['SA_ApertureDiameter'].add(j['Diameter'])
                    metadata['SA_AperturePosX'].add(j['PositionOffset']['x'])
                    metadata['SA_AperturePosY'].add(j['PositionOffset']['y'])

        # Extract preview image
        preview_img = np.asarray(img, dtype='float32')
        preview_image_list['{};{}'.format(tmp_operating_mode, tmp_projector_mode)][tmp_pixel_size_x] = preview_img  # Overwrite previous preview images

        return metadata, preview_image_list

    def extract_metadata_dm3(file_path: str, metadata: dict[str, Union[str, float, int, set]], preview_image_list: dict[str, np.ndarray]):
        """
        Extract metadata from dm3 files.

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
        dict[str, Union[str, float, int, set]], dict[str, np.ndarray]
            The updated metadata and preview image dicts.
        """

        # TODO: Test with STEM and SAED Images
        f = dm3.DM3(file_path)
        allMetadata = f.info

        if allMetadata == '':  # no metadata found
            return metadata

        acq_date = allMetadata['acq_date'].decode('utf-8').split('.')

        metadata['Instrument'] = allMetadata['micro'].decode('utf-8')
        metadata['AcquisitionDateTime'] = '{}-{}-{} {}'.format(acq_date[2], acq_date[1], acq_date[0], allMetadata['acq_time'].decode('utf-8'))
        tmp_operating_mode = allMetadata['OperatingMode'].decode('utf-8')
        metadata['OperatingMode'].add(tmp_operating_mode)
        tmp_projector_mode = allMetadata['ProjectorMode'].decode('utf-8')
        tmp_projector_mode = tmp_projector_mode[0] + tmp_projector_mode[1:].lower()
        metadata['ProjectorMode'].add(tmp_projector_mode)
        metadata['AccelerationVoltage'].add('{} keV'.format(int(float(allMetadata['hv'].decode('utf-8')) // 1000)))
        metadata['Detector'].add(allMetadata['Detector'].decode('utf-8'))
        tmp_pixel_size_x = allMetadata['ScaleX'].decode('utf-8')
        tmp_pixel_size_x += ' ' + allMetadata['UnitX'].decode('utf8')
        metadata['PixelSizeX'].add(tmp_pixel_size_x)
        tmp_pixel_size_y = allMetadata['ScaleY'].decode('utf-8')
        tmp_pixel_size_y += ' ' + allMetadata['UnitY'].decode('utf8')
        metadata['PixelSizeY'].add(tmp_pixel_size_y)
        metadata['Magnification'].add(allMetadata['mag'].decode('utf8'))

        if tmp_operating_mode == 'Diffraction' and tmp_projector_mode != 'STEM':
            metadata['CameraLength'].add(allMetadata['CameraLength'].decode('utf-8'))
            # SA-Aperture setting does not seem to be logged on this instrument or in this file format

        # Extract preview image
        preview_img = np.asarray(f.Image, dtype='float32').copy()
        preview_image_list['{};{}'.format(tmp_operating_mode, tmp_projector_mode)][tmp_pixel_size_x] = preview_img  # Overwrite previous preview images

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

        total = len(preview_image_list['TEM;Imaging']) + len(preview_image_list['STEM;Diffraction']) + len(preview_image_list['TEM;Diffraction'])

        if total == 0:
            exit(-1)

        cols = math.ceil(math.sqrt(total))
        rows = math.ceil(total/cols)

        fig = plt.figure(figsize=(4*cols, 4*rows))
        i = 1

        # TEM Images
        imgs = [(i, preview_image_list['TEM;Imaging'][i]) for i in preview_image_list['TEM;Imaging']]
        imgs.sort(key=lambda t: float(t[0].split(' ')[0]), reverse=True)
        for img in imgs:
            a = fig.add_subplot(rows, cols, i)
            cal = img[0].split(' ')
            img = img[1]
            lb = np.percentile(img, 0.5)
            ub = np.percentile(img, 99.5)
            img = ((img <= lb) * lb) + (img > lb) * img
            img = ((img >= ub) * ub) + (img < ub) * img
            img -= np.min(img)
            img /= np.max(img)
            img *= 255
            a.imshow(img, cmap="gray")
            a.axis('off')
            scalebar = ScaleBar(float(cal[0]), cal[1], length_fraction=0.2, location='lower right', dimension='si-length')
            a.add_artist(scalebar)
            i += 1

        # STEM Images
        imgs = [(i, preview_image_list['STEM;Diffraction'][i]) for i in preview_image_list['STEM;Diffraction']]
        imgs.sort(key=lambda t: float(t[0].split(' ')[0]), reverse=True)
        for img in imgs:
            a = fig.add_subplot(rows, cols, i)
            cal = img[0].split(' ')
            img = img[1]
            lb = np.percentile(img, 0.5)
            ub = np.percentile(img, 99.5)
            img = ((img <= lb) * lb) + (img > lb) * img
            img = ((img >= ub) * ub) + (img < ub) * img
            img -= np.min(img)
            img /= np.max(img)
            img *= 255
            a.imshow(img, cmap="gray")
            a.axis('off')
            scalebar = ScaleBar(float(cal[0]), cal[1], length_fraction=0.2, location='lower right', dimension='si-length')
            a.add_artist(scalebar)
            i += 1

        # ED Images
        imgs = [(i, preview_image_list['TEM;Diffraction'][i]) for i in preview_image_list['TEM;Diffraction']]
        imgs.sort(key=lambda t: float(t[0].split(' ')[0]), reverse=False)
        for img in imgs:
            a = fig.add_subplot(rows, cols, i)
            cal = img[0].split(' ')
            img = img[1]
            lb = np.percentile(img, 0.5)
            ub = np.percentile(img, 99.5)
            img = ((img <= lb) * lb) + (img > lb) * img
            img = ((img >= ub) * ub) + (img < ub) * img
            img -= np.min(img)
            img /= np.max(img)
            img *= 255
            a.imshow(img, cmap="gray")
            a.axis('off')
            scalebar = ScaleBar(float(cal[0]), cal[1], length_fraction=0.2, location='lower right', dimension='si-length-reciprocal')
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
            'AcquisitionDateTime': 'START_DATE',
            'Instrument': 'TEM.INSTRUMENT',
            'OperatingMode': 'TEM.OPERATINGMODE',
            'ProjectorMode': 'TEM.PROJECTORMODE',
            'AccelerationVoltage': 'TEM.ACCELERATIONVOLTAGE',
            'Detector': 'TEM.DETECTOR',
            'PixelSizeX': 'TEM.PIXELSIZEX',
            'PixelSizeY': 'TEM.PIXELSIZEY',
            'ImageSizeX': 'TEM.IMAGESIZEX',
            'ImageSizeY': 'TEM.IMAGESIZEY',
            'Magnification': 'TEM.MAGNIFICATION',
            'CameraLength': 'TEM.CAMERALENGTH',
            'SA_ApertureDiameter': 'TEM.SAED_APERTUREDIAMETER',
            'SA_AperturePosX': 'TEM.SAED_APERTUREPOSX',
            'SA_AperturePosY': 'TEM.SAED_APERTUREPOSY',
            'UserID': 'TEM.OPERATOR',
            'SampleID': 'TEM.SHORT_NAME',
            'SampleDescription': 'TEM.SAMPLE_DESCRIPTION',
            'SpotIndex': 'TEM.SPOT_INDEX',
            'GunLensSetting': 'TEM.GUN_LENS_SETTING',
            'Aperture[C2].Name': 'TEM.C2_APERTURE_NAME',
            'Aperture[OBJ].Name': 'TEM.OBJ_APERTURE_NAME',
        }

        md = {}
        for k in PROPERTY_TYPE_CODE_DICT.keys():
            if k in metadata.keys():
                if isinstance(metadata[k], set):
                    tmp = list(metadata[k])
                    tmp.sort()
                    tmp = ';'.join(tmp)
                else:
                    tmp = metadata[k]
                if len(tmp) > 0:
                    md[PROPERTY_TYPE_CODE_DICT[k]] = tmp

        return md

    for file in files:
        if file.lower().endswith('.tif') or file.lower().endswith('.tiff'):
            metadata, preview_image_list = extract_metadata_tif(file, metadata, preview_image_list)
        elif file.lower().endswith('.emd'):
            metadata, preview_image_list = extract_metadata_emd(file, metadata, preview_image_list)
        elif file.lower().endswith('.dm3'):
            metadata, preview_image_list = extract_metadata_dm3(file, metadata, preview_image_list)

    if len(metadata) == 0:
        return {}

    if create_preview:
        write_preview_image(preview_image_list, os.path.join(os.path.dirname(files[0]), 'TEM_preview.png'))

    return get_metadata_for_openbis(metadata)
