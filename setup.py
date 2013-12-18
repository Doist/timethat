# -*- coding: utf-8 -*-
import os
from setuptools import setup


def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''

setup(
    name='timethat',
    version='0.1',
    author='Roman Imankulov',
    author_email='roman.imankulov@gmail.com',
    description='A benchmark utility',
    license='BSD',
    keywords='benchmark timeit',
    url='http://wedoist.com',
    py_modules=['timethat'],
    long_description=read('README.rst'),
    install_requires=['numpy'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: BSD License',
    ],
)
