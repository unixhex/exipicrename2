# exipicrename2

python3 script for renaming pictures (and matching (raw, xml, txt, ..) files)
on base of embedded exif / iptc data - date, camera name, serial numbers e.g.

reads exif data from pictures and rename them
used exif tags are:
* DateTimeOriginal
* DateTimeOriginal
* FNumber
* ExposureTime
* FocalLength
* Model
* ISOSpeedRatings

Working Platform (beta): Linux
Target Platform (very early dev): Android

developed with python 3.7,
might or might not work with earlier versions of python 3

No waranty it is working for you, too.
**Please make a backup of your files** before testing this.


This programm needs the python library "pillow".

see also: requirements.txt


## Installation

Install with `python3 setup.py install` to your python environment (you might need to use root / sudo for this).
Necessary libraries should be installed automagically, exipicrename will be probably installed to `/usr/bin/expicrename`.

or

whithout root:
`python3 setup.py install --user` will install it to your user python path (e.g. `$HOME/.local/lib/python3.7/site-packages/`). Necessary libraries should
be installed automagically.

For the script `exipicrename` you could add  `$HOME/.local/lib/exipicrename` to your $PATH  ( for bash put following line to .bashrc: `export $PATH=$PATH:/$HOME/.local/lib/expicrename` ).
(Or do create a symlink to `$HOME/bin`)

or

* install python3-pillow (pip, system package)
* copy / symlink `exipicrename.py` to your favourite `$PATH`

## Usage

```
exipicrename {options} [files]
options:

  -h, --help            show this help message and exit
  -d, --datedir         sort and store pictures to sub-directoriesdepending on
                        DateTimeOriginal (YYYY-MM-DD)
  -o, --ooc             use .ooc.jpg as filename extension (for Out Of Cam
                        pictures)
  --oocstring OOCSTRING
                        use string as additional extension, don't forget the
                        '.' as delimiter
  -s, --short, --short-names
                        use short names: only date + serial number, no
                        exhaustive camera data
  -n, --simulate, --dry-run
                        don't rename, just show what would happen
  -V, --version         show the version and exit
  -v, --verbose
  -q, --quiet, --silent
```


Copyright (c) 2019 Hella Breitkopf, https://www.unixwitch.de

MIT License -> see LICENSE file

