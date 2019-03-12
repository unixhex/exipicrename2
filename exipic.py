#!/usr/bin/env python3
"""
exipicrename

reads exif data from pictures
(and later on renames these pictures)

version 2 - except bash with exiftool now with python3 and pillow

status: testing Pillow / early development
"""

import os
# PIL from Pillow
import PIL
#from PIL import Image
#from PIL.ExifTags import TAGS


def print_exif(img):
    """print exif data
    this is a temporary function
    to explore how to create a usefull filename"""

    # https://stackoverflow.com/a/4765242
    exif = {
        PIL.ExifTags.TAGS[k]: v
        for k, v in img._getexif().items()
        if k in PIL.ExifTags.TAGS
    }

    # TODO exception handling if exif-values are missing

    # TODO date + time formating (YYYYmmdd-HHMMSS)

    # TODO fnumber aka aperture (blende)
    # * if the fnmuber is missing (analog lense) you get 0.0 ...
    # * is there a possibility for long floats? -> watch output,
    # it might be better to format output after the decimal point
    blende = exif['FNumber'][0] / exif['FNumber'][1]


    # TODO exposure time (belichtungszeit)
    # I've seen following things in the PIL tuple:
    # 6, 1  -> 6s
    # 1, 125 -> 1/125 s
    # 10, 12500 -> 1/1250 s
    belichtungszeit1 = f"{exif['ExposureTime'][0]}/{exif['ExposureTime'][1]}"
    belichtungszeit2 = exif['ExposureTime'][0] / exif['ExposureTime'][1]

    print(f"date: {exif['DateTimeOriginal']}\n" #foo
          f"kamera: {exif['Model']}\n"
          f"brennweite: {exif['FocalLength']}\n"
          f"belichtungszeit: {belichtungszeit1}\n"
          f"belichtungszeit: {belichtungszeit2}\n"
          f"blende: {blende}\n"
          )


if __name__ == '__main__':

    IMGDIR = "beispiele"
    # DEV ONLY: here we currently expect our example picture dir
    #(directly in our working path)
    # TODO: path as ARG
    for bildname in os.listdir(IMGDIR):
        bild = PIL.Image.open(IMGDIR + "/" + bildname)

        print(30*"-")
        print(bildname)
        print_exif(bild)
