# coding: utf-8

from setuptools import setup, find_packages
try: # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError: # for pip <= 9.0.3
    from pip.req import parse_requirements
    
setup(
    name='lambda-code-storage-monitor',
    version='1.0',
    description='Publishes a custom metric to monitor code storage',
    author='Galen Dunkleberger',
    license='ASL',
    zip_safe=False,
    packages=['lambda_code_storage_monitor'],
    package_dir={'lambda_code_storage_monitor': '.'},
    include_package_data=False,
    install_requires=[
        'lambda_code_storage_monitor==1.0'
    ],
    classifiers=[
        'Programming Language :: Python :: 3.8',
    ],
)
