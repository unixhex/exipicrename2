# exipicrename2

python3 script for renaming pictures (and matching raw files)
on base of embeded exif / iptc data - date, camera name, serial numbers e.g.

Target-Platforms: Linux, Android

Stage of this project: initializing / early development


early beta  of python3 version
seems to work on Linux with python 3.7

No waranty it is working for you, too.
**Please make a backup of your files** before testing this. 


This programm needs the python library "pillow".

see also: requirements.txt


reads exif data from pictures and rename them
used exif tags are:
* DateTimeOriginal
* DateTimeOriginal
* FNumber
* ExposureTime
* FocalLength
* Model
* ISOSpeedRatings

```
usage:
exipicrename {options} [files]
options:
  -h, --help            show help message and exit
  -d, --datedir         sort and store pictures to sub-directories depending on
                        DateTimeOriginal (YYYY-MM-DD)
  -o, --ooc             use .ooc.jpg as filename extension (for Out Of Cam
                        pictures)
  -s, --short           use short names: only date + serial number, no
                        exhaustive camera data
  -n, --simulate, --dry-run
                        don't rename, just show what would happen
  -v, --verbose
  -q, --quiet

```


Copyright (c) 2019 Hella Breitkopf, https://www.unixwitch.de

MIT License -> see LICENSE file
