#!/usr/bin/env python3
"""
exipicrename

reads exif data from pictures
(and later on renames these pictures)

version 2 - except bash with exiftool now with python3 and pillow

status: testing Pillow / early development
"""

import os
import sys
import re
import csv
# PIL from Pillow
import PIL
import PIL.Image
import PIL.ExifTags

# which symbol should be used instead of the decimal delimiter '.' e.g. for aperture (blende)
# since a dot is not good in file names we use something else
DELIMITER = '-'

# camera names sometimes include spaces or komma or other characters which are
# inadvisable for filenames. this is the replacement string if
# such non allowed characters are found in the camera name
SUBSTITUTE = '-'

# if the lens is analog, the value for aperture or length might be zero
# which string should be written instead?
NOVALUE = 'x'

MODEL_TRANSLATE_CSV = "camera-model-rename.csv"
CAMERADICT={}

def print_exif(img):
    """print exif data
    this is a temporary function
    to explore how to create a usefull filename"""
    # fetch tagging from https://stackoverflow.com/a/4765242
    exif = {
        PIL.ExifTags.TAGS[k]: v
        for k, v in img._getexif().items() # pylint: disable=protected-access
        if k in PIL.ExifTags.TAGS
    }

    # TODO exception handling if exif-values are missing

    # TODO date + time formating (YYYYmmdd-HHMMSS)

    _aperture = format_aperture(exif['FNumber'])
    _exposure_time = format_exposuretime_tuple(exif['ExposureTime'])
    _focal_len = format_focal_length_tuple(exif['FocalLength'])
    _camera = format_camera_name(exif['Model'])

    print(f"date: {exif['DateTimeOriginal']}\n"
          # f"camera: {exif['Model']}\n"
          f"camera: {_camera}\n"
          f"Focal Length: {_focal_len}\n"
          f"Exposure Time: {_exposure_time}\n"
          f"Aperture: {_aperture}\n"
          )

def format_camera_name(_name):
    "format camera name - substitute unwanted characters, lower case"
    _newname=re.sub(r'[^a-zA-Z0-9]+', SUBSTITUTE, _name.strip().lower())
    read_model_translate_csv()
    if _newname in CAMERADICT:
        return CAMERADICT[_newname]
    else:
        return _newname


def format_aperture(_tuple):
    "format aperture tuple to short printable string"
    numerator = _tuple[0]  # numerator = zaehler
    divisor = _tuple[1]    # divisor = nenner

    if numerator == 0:
        return NOVALUE

    if numerator % divisor == 0:
        return "f" + str(numerator)

    return "f" + str(numerator/divisor).replace('.', DELIMITER)


def format_focal_length_tuple(_tuple):
    """format FocalLenght tuple to short printable string
    we ignore the position after the decimal point
    because it is usually not very essential for focal length
    """
    numerator = _tuple[0]
    divisor = _tuple[1]

    if numerator == 0:
        return NOVALUE

    if numerator % 10 == 0 and divisor % 10 == 0:
        # example: change 110/10  -> 11
        numerator = numerator // 10
        divisor = divisor // 10

    if divisor == 1:
        # example: change 8/1 to 8mm
        _string = f"{numerator}mm"
    else:
        # example: 524/10 -> 52mm
        # we ignore the position after the decimal point
        # because it is usually not very essential for focal length
        _string = f"{numerator//divisor}mm"
    return _string

def format_exposuretime_tuple(_tuple):
    """format ExposureTime tuple to short printable string
    fractions over or equal 1 second are marked with s, e.g. 8s
    fractions below 1 second are broken down to the divisor,
    this is a bit incorrect but short and common e.g. in cameras
    (and we want to have a short string)
    """
    numerator = _tuple[0]
    divisor = _tuple[1]
    if numerator % 10 == 0 and divisor % 10 == 0:
        # change 10/1250 to 1/125
        numerator = numerator // 10
        divisor = divisor // 10

    if divisor == 1:
        # change 6/1 -> 6s
        # fractions => 1s with s for seconds
        _string = f"{numerator}s"
    else:
        # change 1/125 -> 125
        _string = f"{divisor}"
    return _string


def read_model_translate_csv():
    """read the model translate csv - if available (only once)"""
    if CAMERADICT:
        # we've read the csv already
        return
    try:
        with open(MODEL_TRANSLATE_CSV) as csvfile:
            camera_model_translate = csv.reader(csvfile, delimiter=',')
            for row in camera_model_translate:
                CAMERADICT[row[0]] = row[1]
    except EnvironmentError: # parent of IOError, OSError *and* WindowsError where available
        pass

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

# *** THE END ***
