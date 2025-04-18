"""
Setup script for pangalactic.core
"""
import os, site
from setuptools import setup, find_packages

VERSION = '4.3'

onto_mod_path = os.path.join('pangalactic', 'core', 'ontology')
test_mod_path = os.path.join('pangalactic', 'core', 'test', 'data')
test_data_paths = [os.path.join(test_mod_path, p)
                   for p in os.listdir(test_mod_path)
                   if not p.startswith('__init__')]
vault_mod_path = os.path.join('pangalactic', 'core', 'test', 'vault')
vault_data_paths = [os.path.join(vault_mod_path, p)
                   for p in os.listdir(vault_mod_path)
                   if not p.startswith('__init__')]
ref_db_mod_path = os.path.join('pangalactic', 'core', 'ref_db')
ref_db_paths = [os.path.join(ref_db_mod_path, p)
               for p in os.listdir(ref_db_mod_path)
               if not p.startswith('__init__')]
sitepkg_dir = [p for p in site.getsitepackages()
               if p.endswith('site-packages')][0]

long_description = (
    "An open-source, open-architecture, standards-based application "
    "framework for the development of tools and systems for engineering "
    "data and model integration, collaborative systems engineering, and "
    "multi-disciplinary engineering knowledge capture, integration, "
    "synthesis, and transformation.")

setup(
    name='pangalactic.core',
    version=VERSION,
    description="The Pan Galactic Engineering Framework Core Package",
    long_description=long_description,
    author='Stephen Waterbury',
    author_email='stephen.c.waterbury@nasa.gov',
    maintainer="Stephen Waterbury",
    maintainer_email='waterbug@pangalactic.us',
    license='TBD',
    packages=find_packages(),
    install_requires=[
        'openpyxl',
        'pint',
        'pydispatcher',
        'python-dateutil',
        'pytz',
        'rdflib',
        'ruamel_yaml',
        'sqlalchemy',
        'tzlocal',
        'xlrd',
        'xlwt',
        'xlsxwriter'
        ],
    data_files=[
        # ontology (OWL file)
        (os.path.join(sitepkg_dir, onto_mod_path),
         [os.path.join(onto_mod_path, 'pgef.owl')]),
        # test data files
        (os.path.join(sitepkg_dir, test_mod_path), test_data_paths),
        # test vault files
        (os.path.join(sitepkg_dir, vault_mod_path), vault_data_paths),
        # ref db files
        (os.path.join(sitepkg_dir, ref_db_mod_path), ref_db_paths)
        ],
    zip_safe=False
)

