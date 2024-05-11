#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages
from setuptools.command.install import install as st_install

import os
import shutil

try:
    from pypandoc import convert
except ImportError:
    def convert(filename, fmt):
        with open(filename) as fd:
            return fd.read()


class install(st_install):
    def _post_install(self, lib_dir):
        packages = ('edw', 'email_auth', 'social_extra')
        backend_dir = os.path.join(lib_dir, 'backend')
        if os.path.exists(backend_dir):
            for package in packages:
                src_dir = os.path.join(backend_dir, package)
                dst_dir = os.path.join(lib_dir, package)
                if os.path.exists(dst_dir):
                    shutil.rmtree(dst_dir)
                shutil.copytree(src_dir, dst_dir, symlinks=True)
            if os.path.exists(backend_dir):
                shutil.rmtree(backend_dir)

    def run(self):
        st_install.run(self)
        self.execute(self._post_install, (self.install_lib,),
                     msg="Running post install task")


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
    author="InfoLabs LLC",
    author_email="team@infolabs.ru",
    name="django-edw",
    version='0.2.0',
    description="A RESTful Django Enterprise Data Warehouse",
    long_description=convert('README.md', 'rst'),
    url='https://bitbucket.org/info-labs/django-edw.git',
    license='GPL v3 License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(exclude=['docs', 'requirements']),
    package_dir={
        'edw': 'backend/edw',
        'email_auth': 'backend/email_auth',
        'social_extra': 'backend/social_extra',
    },
    include_package_data=True,
    zip_safe=False,
    cmdclass={
        'install': install
    },
    install_requires=[
        'Django>=1.9,<4.0',
        'djangorestframework>=3.3',
        'django-filer>=1.0.6',
        'django-fsm>=2.4.0',
        'django-rest-auth>=0.5.0',
        'django-select2>=5.5.0',
        'djangorestframework-recursive>=0.1.2',
        'djangorestframework-filters>=0.11.1',
        'django-polymorphic>=1.1',
    ],
)
