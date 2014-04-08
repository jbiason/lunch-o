#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages
from luncho import VERSION

setup(name='luncho',
      version=VERSION,
      description='Democratic lunching',
      long_description=file('README.md').read(),
      author='Julio Biason',
      author_email='julio.biason@gmail.com',
      url='https://github.com/jbiason/lunch-o',
      packages=find_packages(),
      install_requires=file('requirements.txt').readlines(),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Web Environment',
          'Framework :: Flask',
          'Intended Audience :: End Users/Desktop',
          'Programming Language :: Python',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Internet :: WWW/HTTP :: WSGI',
          'Topic :: Utilities',
          'Operating System :: OS Independent'
      ])
