========
DataStore Generic Uploader
========

A Data Store upload helper with flexible choice of object types and their parents/children dependencies. Based on Bastian Rühles https://github.com/BAMresearch/openbis-upload-helper which is a simple upload tool for [OpenBIS](https://openbis.ch/) that parses metadata from the specified files, creates a preview of the data, and uploads the files and preview images along with the metadata to `OpenBIS`.

The structure of the metadata and some upload settings are specific to the `OpenBIS` instance used at [BAM](https://www.bam.de) and the [BAM Data Store](https://www.bam.de/Content/DE/Projekte/laufend/BAM-Data-Store/bam-data-store.html).

This program is in active development and subject to change. The description will be adjusted accordingly.

.. start-badges

| |version| |commits-since| |license|
| |supported-versions| |wheel| |downloads|
| |cicd| |coverage|

.. |version| image:: https://img.shields.io/pypi/v/datastore-generic-uploader.svg
    :target: https://test.pypi.org/project/datastore-generic-uploader
    :alt: PyPI Package latest release

.. |commits-since| image:: https://img.shields.io/github/commits-since/BAMresearch/datastore-generic-uploader/v0.1.0.svg
    :target: https://github.com/BAMresearch/datastore-generic-uploader/compare/v0.1.0...main
    :alt: Commits since latest release

.. |license| image:: https://img.shields.io/pypi/l/datastore-generic-uploader.svg
    :target: https://en.wikipedia.org/wiki/MIT_license
    :alt: License

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/datastore-generic-uploader.svg
    :target: https://test.pypi.org/project/datastore-generic-uploader
    :alt: Supported versions

.. |wheel| image:: https://img.shields.io/pypi/wheel/datastore-generic-uploader.svg
    :target: https://test.pypi.org/project/datastore-generic-uploader#files
    :alt: PyPI Wheel

.. |downloads| image:: https://img.shields.io/pypi/dw/datastore-generic-uploader.svg
    :target: https://test.pypi.org/project/datastore-generic-uploader/
    :alt: Weekly PyPI downloads

.. |cicd| image:: https://github.com/BAMresearch/datastore-generic-uploader/actions/workflows/ci-cd.yml/badge.svg
    :target: https://github.com/BAMresearch/datastore-generic-uploader/actions/workflows/ci-cd.yml
    :alt: Continuous Integration and Deployment Status

.. |coverage| image:: https://img.shields.io/endpoint?url=https://BAMresearch.github.io/datastore-generic-uploader/coverage-report/cov.json
    :target: https://BAMresearch.github.io/datastore-generic-uploader/coverage-report/
    :alt: Coverage report

.. end-badges


Installation
============

::

    pip install datastore-generic-uploader

You can also install the in-development version with::

    pip install git+https://github.com/BAMresearch/datastore-generic-uploader.git@main


Documentation
=============

https://BAMresearch.github.io/datastore-generic-uploader

![](Documentation/GUI.jpg)

Folder Structure
----------------
- **Main Folder:** The Python Code for the Graphical User Interface, files specifying the requirements and license, and this readme file
- **Parser:** Collection of classes for parsing metadata from different files (a list of currently implemented parsers can be found [here](#parsers-that-are-currently-implemented))
- **Documentation:** Additional resources used in this documentation

Installation (fixme)
------------
Clone (or download) the repository, set up and activate a virtual environment, and install the packages from `requirements.txt`. For Windows::

    git clone https://github.com/BAMresearch/datastore-generic-uploader
    cd datastore-generic-uploader
    python -m venv .\venv
    venv\Scripts\activate
    pip install -r requirements.txt

How to run (fixme)
----------
After installation, the program can be run by simply double-clicking the `OpenBISUploadHelper.bat` file (on Windows), or by activating the virtual environment and running the script from the command line. For Windows::

    cd datastore-generic-uploader/src
    venv\Scripts\activate
    python -m datastore-generic-uploader

How to use
----------
- Select the file(s) you want to upload by clicking on the three dots `...` next to the text field for `Files`
- You can select whether you want to create a `Preview Image` (selected by default), create a `Metadata File` (disabled by default), and upload everything to `OpenBIS` (selected by default). If you select the second option, the parsed metadata will be written to a file (you can use this option and disable the upload if you are only interested in extracting metadata with the parsers).
- Enter your User Name. The script can be configured to automatically select the default Space Name and Project Name for this user (see source code for an example)
- Enter your Password (will be hidden with `*` characters)
- Select the `Space Name` from the dropdown list (or type it into the field)
- Select the `Project Name` from the dropdown list (or type it into the field)
- Give the `Experiment Name` to which these files belong
- Click on `Export`

This will automatically create a new `Experimental Step` matching the type of characterization data you selected in the specified `Experiment` of the `Prject` in the `Space` selected above. If the `Experiment` does not exist, it will be created automatically. The program will then attempt to find the right parser to use with these data, extract the metadata, create a preview image and/or metadata file (if the corresponding options were selected above), and upload everything to `OpenBIS`, filling the metadata fields of the `Experimental Step` accordingly. The program can also be configured to automatically set the `parents` for this `Experimental Step` to the corresponding `Instrument` from the `OpenBIS Inventory` (see source code for an example)

Parsers that are currently implemented
--------------
- **Infrared Spectroscopy Data**, exported as csv from ThermoFischer Scientific OMNIC Software
- **Nuclear Magnetic Resonance Spectroscopy Data**, saved as JCAMP-DX files by Oxford Instruments SpinFlow Software for the XPulse instrument
- **Scanning Electron Microscopy Image Data**, saved as tif files by the Software of the Zeiss Supra 40 SEM
- **Transmission Electron Microscopy Image Data**:
  - Saved as tif files by the Software of the ThermoFisher Scientific Talos F200S
  - Saved as emd files by the Software of the ThermoFisher Scientific Talos F200S
  - Saved as dm3 files by the Software of the JEOL JEM-2200FS TEM
- **Optical Spectroscopy Data**, exported as txt from the SoftMax Pro Software of the MolecularDevices Spectramax Platereader
- **Dynamic Light Scattering data**, exported as csv from Malvern Zetasizer Instruments (Legacy) - For export from SQL Databases of the current Software, see [here](https://github.com/BAMresearch/MAPz_at_BAM/blob/main/Minerva/Hardware/OtherHardware/MalvernPanalytical.py)

License
--------
- The code for the Upload Helper Tool and the parsers are published under the [MIT license](https://opensource.org/license/mit).
- The code for parsing DM3 files is a slightly modified version of the code from Pierre-Ivan Raynal, published on [Github](https://github.com/piraynal/pyDM3reader) under the [MIT license](https://opensource.org/license/mit).

Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
