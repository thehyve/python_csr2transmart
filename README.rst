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
that can be loaded into TranSMART_ platform,
an open source data sharing and analytics platform for translational biomedical research.

The output of the transformation is a collection of tab-separated files that can be loaded into
a TranSMART database using the transmart-copy_ tool.

.. _TranSMART: https://github.com/thehyve/transmart_core
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


Usage
------

TODO: Add example


Python versions
---------------

This repository is set up with Python version 3.6


Package management and dependencies
-----------------------------------

This project uses `pip` for installing dependencies and package management.

* Dependencies should be added to `setup.py` in the `install_requires` list.

Testing and code coverage
-------------------------

* Tests are in the ``tests`` folder.

* The ``tests`` folder contains:

  - A test if the `csr2transmart` script starts (file: ``test_csr2transmart``)
  - A test that checks whether your code conforms to the Python style guide (PEP 8) (file: ``test_lint.py``)

* The testing framework used is `PyTest <https://pytest.org>`_

* Tests can be run with ``python setup.py test``

Coding style conventions and code quality
-----------------------------------------

* Check your code style with ``prospector``

* You may need run ``pip install .[dev]`` first, to install the required dependencies


License
*******

Copyright (c) 2019 The Hyve B.V.

The CSR to TranSMART loader is licensed under the MIT License. See the file `<LICENSE>`_.
