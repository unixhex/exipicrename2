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
-v or --verbose   print some info while working
-q or --quite     as silent as possible
-h or --help      print this help
-d or --datedir   write the files in a YYYY-mm-dd directory
-s or --simulate  don't rename (use with --verbose to see what would happen
-o or --ooc       all matching JPG files get the extension .ooc.jpg (out of cam)
```


Copyright (c) 2019 Hella Breitkopf, https://www.unixwitch.de

MIT License -> see LICENSE file
