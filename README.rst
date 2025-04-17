========
Overview
========

A Data Store upload helper with flexible choice of object types and their parents/children dependencies.

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
