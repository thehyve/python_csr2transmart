CSR to TranSMART loader
=======================

|Build status| |codecov| |pypi| |status| |license|

.. |Build status| image:: https://travis-ci.org/thehyve/python_csr2transmart.svg?branch=master
   :alt: Build status
   :target: https://travis-ci.org/thehyve/python_csr2transmart/branches
.. |codecov| image:: https://codecov.io/gh/thehyve/python_csr2transmart/branch/master/graph/badge.svg
   :alt: codecov
   :target: https://codecov.io/gh/thehyve/python_csr2transmart
.. |pypi| image:: https://img.shields.io/pypi/v/csr2transmart.svg
   :alt: PyPI
   :target: https://pypi.org/project/csr2transmart/
.. |status| image:: https://img.shields.io/pypi/status/csr2transmart.svg
   :alt: PyPI - Status
.. |license| image:: https://img.shields.io/pypi/l/csr2transmart.svg
   :alt: MIT license
   :target: LICENSE

This package contains a script that transforms Central Subject Registry data to a format
that can be loaded into the TranSMART_ platform,
an open source data sharing and analytics platform for translational biomedical research.

The output of the transformation is a collection of tab-separated files that can be loaded into
a TranSMART database using the transmart-copy_ tool.

.. _TranSMART: https://github.com/thehyve/transmart-core
.. _transmart-copy: https://github.com/thehyve/transmart-core/tree/dev/transmart-copy

⚠️ Note: this is a very preliminary version, still under development.
Issues can be reported at https://github.com/thehyve/python_csr2transmart/issues.


Installation and usage
**********************

To install csr2transmart, do:

.. code-block:: console

  pip install csr2transmart

or from sources:

.. code-block:: console

  git clone https://github.com/thehyve/python_csr2transmart.git
  cd python_csr2transmart
  pip install .


Data model
----------

The Central Subject Registry (CSR) data model contains individual,
diagnosis, biosource and biomaterial entities. The data model is defined
as a data class in `csr/csr.py`_

.. _`csr/csr.py`: https://github.com/thehyve/python_csr2transmart/blob/master/csr/csr.py

Usage
------

This repository contains a number of command line tools:

* ``sources2csr``: Reads from source files and produces tab delimited CSR files.
* ``csr2transmart``: Reads CSR files and transforms the data to the TranSMART data model,
  creating files that can be imported to TranSMART using `transmart-copy`.
* ``csr2cbioportal``: Reads CSR files and transforms the data to patient and sample files
  to imported into cBioPortal.

``sources2csr``
~~~~~~~~~~~~~~~

.. code-block:: console

  sources2csr <input_dir> <output_dir> <config_dir>

The tool reads input files from ``<input_dir>`` and
writes CSR files in tab-delimited format (one file per entity type) to
``<output_dir>``.
The output directory ``<output_dir>`` needs to be either empty or not yet existing.

The sources configuration will be read from ``<config_dir>/sources_config.json``,
a JSON file that contains two attributes:

* ``entities``: a map from entity type name to a description of the sources for that entity type. E.g.,

  .. code-block:: json

    {
      "Individual": {
        "attributes": [
          {
            "name": "individual_id",
            "sources": [
              {
                "file": "individual.tsv",
                "column": "individual_id"
              }
            ]
          },
          {
            "name": "birth_date",
            "sources": [
              {
                "file": "individual.tsv",
                "date_format": "%d-%m-%Y"
              }
            ]
          }
        ]
      }
    }

  The entity type names have to match the entity type names in the CSR data model and
  the attribute names should match the attribute names in the data model as well.
  The ``column`` field is optional, by default the column name is assumed to be
  the same as the attribute name.
  For date fields, a ``date_format`` can be specified. If not specified, it is
  assumed to be ``%Y-%m-%d`` or any other `date formats supported by Pydantic`_.
  If multiple input files are specified for an attribute, data for that attribute
  is read in that order, i.e., only if the first file has no data for an attribute
  for a specific entity, data for that attribute for that entity is read from the next file, etc.

* ``codebooks``: a map from input file name to codebook file name, e.g., ``{"individual.tsv": "codebook.txt"}``.

* ``file_format``: a map from input file name to file format configuration,
  which allows you to configure the delimiter character (default: ``\t``).
  E.g., ``{"individual.tsv": {"delimiter": ","}}``.

See `test_data/input_data/config/sources_config.json`_ for an example.

Content of the codebook files has to match the following format:

*   First a header line with a number and column names the codes apply to. 
    The first field has a number, the second field a space separated list of column names, e.g., ``1\tSEX GENDER``.
*   The lines following the header start with an empty field. 
    Then the lines follow the format of ``code\tvalue`` until the end of the line, 
    e.g., ``\t1\tMale\t2\tFemale``.
*   The start of a new header, which is detected by the first field not being empty 
    starts the process over again.

See `<test_data/input_data/codebooks/valid_codebook.txt>`_ for a codebook file example.

.. _`date formats supported by Pydantic`: https://pydantic-docs.helpmanual.io/#datetime-types
.. _`test_data/input_data/config/sources_config.json`: https://github.com/thehyve/python_csr2transmart/blob/master/test_data/input_data/config/sources_config.json


``csr2transmart``
~~~~~~~~~~~~~~~~~

.. code-block:: console

  csr2transmart <input_dir> <output_dir> <config_dir>

The tool reads CSR files from ``<input_dir>`` (one file per entity type),
transforms the CSR data to the TranSMART data model. 
In addition, if there is an ``NGS`` folder inside ``<input_dir>``, 
the tool will read the NGS files inside to determine values of additional CSR biomaterial variables.
The tool writes the output in ``transmart-copy`` format to ``<output_dir>``.
The output directory ``<output_dir>`` needs to be either empty or not yet existing.

The ontology configuration will be read from ``<config_dir>/ontology_config.json``.
See `test_data/input_data/config/ontology_config.json`_ for an example.

.. _`test_data/input_data/config/ontology_config.json`: https://github.com/thehyve/python_csr2transmart/blob/master/test_data/input_data/config/ontology_config.json


``csr2cbioportal``
~~~~~~~~~~~~~~~~~~

.. code-block:: console

  csr2cbioportal <input_dir> <ngs_dir> <output_dir>

The tool reads CSR files from ``<input_dir>`` (one file per entity type),
and NGS data (genomics data) from ``<ngs_dir>``,
transforms the CSR data to the clinical data format for cBioPortal and
writes the following data types to ``<output_dir>``:

* Clinical data 
* Mutation data
* CNA Segment data
* CNA Continuous data
* CNA Discrete data

File structure, case lists and meta files will also be added to the output folder.
See the  `cBioPortal file formats`_ documentation for further details.

The output directory ``<output_dir>`` needs to be either empty or not yet existing.

.. _`cBioPortal file formats`: https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats

Source data assumptions and validation
--------------------------------------

General file characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``Delimiter`` The source data should be provided as delimited text files. The delimiter can be `configured`_ per 
  data file. If not configured, a tab-delimited file is assumed.
* ``Comments`` Comment lines may be present, indicated by a ``#`` as the first character. These lines will be ignored.
* ``Header`` The first non-comment line is assumed to be the header. It should be exactly one line.
* ``Field number`` The number of fields (columns) is determined by the header. Every other line in the file 
  should have this same number of fields (no blank lines).
* ``Whitespace`` Leading or trailing whitespace is not trimmed. If present, it will persist in the final observation.
* ``Encoding`` All files are assumed to be utf-8 encoded.

CSR entities
~~~~~~~~~~~~

All characteristics and relationships of the CSR data model are defined in `csr/csr.py`_. Any field present in the
source data that you would like to load to tranSMART, must be linked to a CSR field via the sources_config. Additional
fields not present in the sources_config will be ignored.

Regarding the source data, we can distinguish four types of validation:

1. Value validation: Independent validation of a single field value. This comprises type validation (e.g. string, integer or date), nullability (whether a field may be empty), and unique constraints.
2. Record validation: Validation across different fields from the same record within the same entity. This validation is relevant when the validity of a field value is dependent on the other fields of the same record (e.g. a biosource record with src_biosource_id = BS1, is invalid when biosource_id = BS1).
3. Entity validation: Concerns the integrity check of all records within a single entity (e.g. do all src_biosource_id values also have corresponding biosource_id records within the biosource entity).
4. Across-entity validation Checks the validity of relationships between records of different entities.

The data validation of the current pipeline is implemented for type 1 and to a limited extent for type 2 and 4.
Hence, the source data is assumed to be coherent regarding its relationships within the same entity and across
different entities. While erroneous relationships across entities, in respect of missing entity records, will be
detected (e.g. a biomaterial linked to a non-existing biosource), logically impossible relationships are not (e.g.
biomaterial BM2 is derived from BM1, but from a different biosource).

Any entity records that cannot be linked to an individual through its relationships, will not end up in tranSMART (e.g. 
a study that is present in the Study entity, but not in individual_study). Additionally, any individual needs to have at
least one observation to be included. This means that merely a collection of related ID values, without observations
linked to any of those IDs, will not become available in tranSMART.

.. _`configured`: test_data/input_data/config/sources_config.json#L390


Python versions
---------------

This package supports Python versions 3.6 and 3.7.


Package management and dependencies
-----------------------------------

This project uses `pip` for installing dependencies and package management.

* Dependencies should be added to `requirements.txt`_.

.. _`requirements.txt`: https://github.com/thehyve/python_csr2transmart/blob/master/requirements.txt

Testing and code coverage
-------------------------

* Tests are in the ``tests`` folder.

* The ``tests`` folder contains tests for each of the tools and
  a test that checks whether your code conforms to the Python style guide (PEP 8) (file: ``test_lint.py``)

* The testing framework used is `PyTest <https://pytest.org>`_

* Tests can be run with ``python setup.py test``

Coding style conventions and code quality
-----------------------------------------

* Check your code style with ``prospector``

* You may need run ``pip install .[dev]`` first, to install the required dependencies


License
*******

Copyright (c) 2019 The Hyve B.V.

The CSR to TranSMART loader is licensed under the MIT License. See the file LICENSE_.

.. _LICENSE: https://github.com/thehyve/python_csr2transmart/blob/master/LICENSE
