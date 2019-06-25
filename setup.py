#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from setuptools import setup

if sys.version_info < (3, 6):
    sys.exit(
        'Python < 3.6 is not supported. You are using Python {}.{}.'.format(
            sys.version_info[0], sys.version_info[1])
    )

here = os.path.abspath(os.path.dirname(__file__))

# To update the package version number, edit csr2transmart/__version__.py
version = {}
with open(os.path.join(here, 'csr2transmart', '__version__.py')) as f:
    exec(f.read(), version)

with open('requirements.txt', 'r') as f:
    required_packages = f.read().splitlines()

setup(
    name='csr2transmart',
    version=version['__version__'],
    description="Script to load CSR data to TranSMART",
    author="Gijs Kant",
    author_email='gijs@thehyve.nl',
    url='https://github.com/thehyve/csr2transmart',
    packages=[
        'csr2transmart',
    ],
    package_dir={'csr2transmart': 'csr2transmart'},
    entry_points={
        'console_scripts': ['csr2transmart=csr2transmart.csr2transmart:main'],
    },
    include_package_data=True,
    license="MIT",
    zip_safe=False,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    python_requires='>=3.6.0',
    install_requires=required_packages,
    setup_requires=[
        # dependency for `python setup.py test`
        'pytest-runner',
        # dependency for `python setup.py bdist_wheel`
        'wheel'
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'pycodestyle',
    ],
    extras_require={
        'dev':  ['prospector[with_pyroma]', 'yapf', 'isort'],
    }
)
