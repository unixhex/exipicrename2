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

install with python3 setup.py to your python environment
or put exipicrename.py to your favourite $PATH 

```
usage:
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
  -v, --verbose
  -q, --quiet, --silent
```


Copyright (c) 2019 Hella Breitkopf, https://www.unixwitch.de

MIT License -> see LICENSE file

