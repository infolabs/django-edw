#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages
import shop
try:
    from pypandoc import convert
except ImportError:
    def convert(filename, fmt):
        with open(filename) as fd:
            return fd.read()

CLASSIFIERS = [
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
]

setup(
    author="Excentrics LLC",
    author_email="info@excentrics.ru",
    name="django-edw",
    version=edw.__version__,
    description="A RESTful Django Enterprise Data Warehouse",
    long_description=convert('README.md', 'rst'),
    url='http://excentrics.github.io/django-edw',
    license='GPL v3 License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(exclude=['example', 'docs']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Django>=1.9,<1.10',
        'djangorestframework>=3.1',
        'beautifulsoup4>=4.4.0',
        'django-filer>=1.0.6',
        #'django-ipware>=1.1.1',
        'django-fsm>=2.2.1',
        'django-rest-auth>=0.5.0',
        'django-angular>=0.7.15',
        #'django-select2>=5.5.0',
        #'django-sass-processor>=0.3.4',
    ],
)