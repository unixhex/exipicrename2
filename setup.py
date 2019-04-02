from setuptools import setup

def readme():
    with open("README.md", "r") as fh:
        long_description = fh.read()


setup(
    name='exipicrename',
    version='0.2',
    description='renaming pictures (and matching raw files) on embeded exif',
    long_description=readme(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Topic :: Image Processing :: Renaming',
      ],
    url='https://github.com/unixhex/exipicrename2',
    author='Hella Breitkopf',
    licence='MIT',
    packages=['exipicrename'],
    install_requires=[
        'pillow',
    ],
    entry_points = {
        'console_scripts'=['expicrename=exipicrename.exipicrename:main'],
        },
    include_package_data=True,
    zip_safe=False,
    )
