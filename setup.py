#!/usr/bin/env python2
"""
Setup for the c64img
"""
from distutils.core import setup

from c64img import __version__ as ver


setup(name='c64img',
      packages=['c64img'],
      version=ver,
      description='Image processing and converter for C64 graphic formats',
      author='Roman Dobosz',
      author_email='gryf73@gmail.com',
      url='https://bitbucket.org/gryf/image2c64',
      download_url='https://bitbucket.org/gryf/image2c64.git',
      keywords=['c64', 'image', 'converter', 'koala', 'Art Studio', 'raw'],
      install_requires=['Pillow'],
      scripts=['scripts/image2c64'],
      classifiers=['Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 2 :: Only',
                   'Development Status :: 5 - Stable',
                   'Environment :: Console',
                   'Intended Audience :: End Users/Desktop',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Topic :: Multimedia :: Graphics',
                   'Topic :: Multimedia :: Graphics :: Graphics Conversion'],
      long_description=open('README.rst').read(),
      options={'test': {'verbose': False,
                        'coverage': False}})
