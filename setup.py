#!/usr/bin/env python

from setuptools import setup
import exipicrename

def readme():
    with open("README.md", "r") as fh:
        long_description = fh.read()
    return long_description


setup(
    name='exipicrename',
    version=exipicrename.version,
    description='renaming pictures (and matching raw files) on embeded exif',
    long_description=readme(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Topic :: Utilities',
      ],
    url='https://github.com/unixhex/exipicrename2',
    author='Hella Breitkopf',
    author_email="exipicrename@unixwitch.de",
    license='MIT',
    packages=['exipicrename'],
    platforms=['Linux'],
    install_requires=[
        'pillow',
    ],
    entry_points = {
        'console_scripts': ['exipicrename=exipicrename.exipicrename:main'],
        },
    include_package_data=True,
    zip_safe=False,
    )
