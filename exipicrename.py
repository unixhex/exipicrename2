#!/usr/bin/env python3
"""
exipicrename

Early beta  of python3 version.

Reads exif data from pictures and rename them.

Used exif tags are:
* DateTimeOriginal
* FNumber
* ExposureTime
* FocalLength
* Model
* ISOSpeedRatings

"""

# Copyright (c) 2019 Hella Breitkopf, https://www.unixwitch.de
# MIT License -> see LICENSE file


import os
from os.path import splitext as splitext_last
import sys
import re
import csv
import time
import glob
import argparse
# PIL from Pillow
import PIL
import PIL.Image
import PIL.ExifTags

try:
    from pysize import get_size as getmemsize #just for debugging
    # pysize from https://github.com/bosswissam/pysize
except ModuleNotFoundError:
    pass

# which symbol should be used instead of the decimal delimiter '.' e.g. for aperture (blende)
# since a dot is not good in file names we use something else
DELIMITER = '-'

# camera names sometimes include spaces or komma or other characters which are
# inadvisable for filenames. this is the replacement string if
# such non-allowed characters are found in the camera name
SUBSTITUTE = '-'

# if the lens is analog, the value for aperture or length might be zero
# which string should be written instead?
NOVALUE = 'x'

# we include a serial number into the filename. This is the default length, if neccessary that
# number gets more digits (depending how much files are renamed on that run).
SERIAL_LENGTH = 3

MODEL_TRANSLATE_CSV = "camera-model-rename.csv"

CAMERADICT = {}
PIC_DICT = {}

__FILELIST = []
__MAKEDATEDIR = False
__VERBOSE = False
__QUIET = False
__SIMULATE = False
__OOC = False
__SHORT = False
__DATEDIR = ''

# this extensions we read as JPEG
JPG_ORIG_EXTENSIONS = ('.jpg', '.JPG', '.jpeg', '.JPEG')

# this extension we use as output JPEG extension
JPG_EXTENSION = '.jpg'


# source https://fileinfo.com/filetypes/camera_raw
RAW_EXTENSIONS = (
    '.orf', '.ORF', '.3fr', '.3FR',
    '.ari', '.ARI', '.arw', '.ARW',
    '.bay', '.BAY',
    '.cr2', '.CR2', '.cr3', '.CR3', '.crw', '.CRW', '.cs1', '.CS1', '.cxi', '.CXI',
    '.dcr', '.DCR', '.dng', '.DNG',
    '.eip', '.EIP', '.erf', '.ERF',
    '.fff', '.FFF',
    '.iiq', '.IIQ',
    '.j6i', '.J6I',
    '.k25', '.K25', '.kdc', '.KDC',
    '.mef', '.MEF', '.mfw', '.MFW', '.mos', '.MOS', '.mrw', '.MRW',
    '.nef', '.NEF', '.nrw', '.NRW',
    '.pef', '.PEF',
    '.raf', '.RAF', '.raw', '.RAW', '.rw2', '.RW2', '.rwl', '.RWL', '.rwz', '.RWZ',
    '.sr2', '.SR2', '.srf', '.SRF', '.srw', '.SRW',
    '.x3f', '.X3F',
)



def create_new_basename(img):
    """create a new filename based on exif data"""
    # fetch tagging from https://stackoverflow.com/a/4765242
    try:
        exif = {
            PIL.ExifTags.TAGS[k]: v
            for k, v in img._getexif().items() # pylint: disable=protected-access
            if k in PIL.ExifTags.TAGS
        }
    except AttributeError:
        if __VERBOSE:
            print('NO exif info in ' + img.filename, file=sys.stderr)
        return None, None, None

    try:
        _datetime = format_datetime(exif['DateTimeOriginal'])
        _date = format_date(exif['DateTimeOriginal'])
        if not __SHORT:
            _aperture = format_aperture(exif['FNumber'])
            _exposure_time = format_exposuretime_tuple(exif['ExposureTime'])
            _focal_len = format_focal_length_tuple(exif['FocalLength'])
            _camera = format_camera_name(exif['Model'])
            _iso = (exif['ISOSpeedRatings'])
    except KeyError:
        if __VERBOSE:
            print('(Some) exif tags missing in ' + img.filename, file=sys.stderr)
        return None, None, None

    if not __SHORT:
        _new_basename = f"{_datetime}__{{}}__{_camera}__{_focal_len}__{_aperture}__iso{_iso}"
    else:
        _new_basename = f"{_datetime}__{{}}"

    return _datetime, _new_basename, _date

def format_camera_name(_name):
    """format camera name - substitute unwanted characters, lower case
    if available, read translations for camera models from csv and apply them """
    _newname = re.sub(r'[^a-zA-Z0-9]+', SUBSTITUTE, _name.strip().lower())
    read_model_translate_csv()
    if _newname in CAMERADICT:
        return CAMERADICT[_newname]

    return _newname


def format_aperture(_tuple):
    "format aperture tuple to short printable string"
    numerator = _tuple[0]  # numerator = zaehler
    divisor = _tuple[1]    # divisor = nenner

    if numerator == 0:
        return NOVALUE

    if numerator % divisor == 0:
        return "f" + str(numerator//divisor)

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


def format_datetime(_datetime):
    """format time string -> YYYYmmdd_HHMMSS"""
    _time_struct = time.strptime(_datetime, "%Y:%m:%d %H:%M:%S")
    return time.strftime("%Y%m%d_%H%M%S", _time_struct)

def format_date(_datetime):
    """format time string -> YYYY-mm-dd"""
    _time_struct = time.strptime(_datetime, "%Y:%m:%d %H:%M:%S")
    return time.strftime("%Y-%m-%d", _time_struct)


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
    except OSError:
        pass

def splitext_all(_filename):
    """split all extensions (after the first .) from the filename
    should work similar to os.path.splitext (but that splits only the last extension)
    """
    _name, _extensions = _filename.split('.')[0], '.'.join(_filename.split('.')[1:])
    return(_name, "."+ _extensions)


def picdict_set_serial_once(_pic, _serial, _serial_length):
    """set serial number in a global PIC_DICT dictionary entry (if not set yet or if empty)"""
    # make a string out of "SERIAL", fill it up with 0 up to SERIAL_LENGTH
    # include it into the new file base name
    try:
        _ = PIC_DICT[_pic]['serial']
        return False
    except KeyError:
        pass

    PIC_DICT[_pic]['serial'] = _serial
    PIC_DICT[_pic]['new_basename'] = \
        PIC_DICT[_pic]['new_basename'].format(str(_serial).zfill(_serial_length))
    return True

def picdict_has_orig_filepath(filepath):
    """search if this filename is already recorded in global PIC_DICT"""
    for filerecord in PIC_DICT.values():
        try:
            if filerecord['orig_filename'] == filepath:
                return True
        except KeyError:
            pass
        return False


def rename_files():
    """rename files (after check if we don't overwrite)"""
    for k in sorted(PIC_DICT):

        oldname = "{}/{}{}".format(
            PIC_DICT[k]["orig_dirname"],
            PIC_DICT[k]["orig_basename"],
            PIC_DICT[k]["orig_extension"],
            )
        newname = "{}/{}{}".format(
            PIC_DICT[k]["new_dirname"],
            PIC_DICT[k]["new_basename"],
            PIC_DICT[k]["new_extension"],
            )

        if oldname == newname:
            continue

        if not os.path.isfile(oldname) and not __QUIET:
            print(f"WARNING: want to rename {oldname}\n"
                  f"                     to {newname}\n"
                  f"         but orig file not available any more", file=sys.stderr)
            continue
        if os.path.isfile(newname) and not __QUIET:
            print(f"WARNING: did not overwrite existing file\n"
                  f"\t{newname}\n\twith:\n"
                  f"\t{oldname}", file=sys.stderr)
            continue
            sys.exit()  # pylint: disable=unreachable
            # we really really don't want to overwrite files

        if __VERBOSE:
            msg = ""
        if __SIMULATE:
            msg = "SIMULATION| "
        if __VERBOSE or (__SIMULATE and not __QUIET):
            print(f"{msg}rename old: {oldname} ")
            print(f"{msg}to NEW    : {newname} ")

        if not __SIMULATE:
            os.rename(oldname, newname)


def __parse_args():
    "read and interpret commandline arguments with argparse"

    # I know, globals are not fine. but everything
    # else suggested e.g. in https://docs.python.org/3.7/faq/programming.html
    # is in this case more complex, less clear, much more complicate to handle
    # and more error prone (I am open to suggestions)
    global __VERBOSE            # pylint: disable=global-statement
    global __FILELIST           # pylint: disable=global-statement
    global __MAKEDATEDIR        # pylint: disable=global-statement
    global __SIMULATE           # pylint: disable=global-statement
    global __QUIET              # pylint: disable=global-statement
    global __OOC                # pylint: disable=global-statement
    global __SHORT              # pylint: disable=global-statement

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        )
    parser.add_argument("file", nargs='+',
                        help="jpeg files to rename")
    parser.add_argument("-d", "--datedir", action="store_true",
                        help="sort and store pictures to sub-directories"
                        "depending on DateTimeOriginal (YYYY-MM-DD) ")
    parser.add_argument("-o", "--ooc", action="store_true",
                        help="use .ooc.jpg as filename extension (for Out Of Cam pictures)")
    parser.add_argument("-s", "--short", action="store_true",
                        help="use short names: only date + serial number,"
                        " no exhaustive camera data")
    parser.add_argument("-n", "--simulate", "--dry-run", action="store_true",
                        help="don't rename, just show what would happen")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args()
    if args.quiet:
        __VERBOSE = False
        __QUIET = True
    if args.datedir:
        __MAKEDATEDIR = True
    if args.simulate:
        __SIMULATE = True
    if args.ooc:
        __OOC = True
    if args.short:
        __SHORT = True
    if args.verbose:
        __VERBOSE = True
        print(f"""FLAGS:
        verbose: {__VERBOSE}
        quiet: {__QUIET}
        makedatedir: {__MAKEDATEDIR},
        simulate: {__SIMULATE}
        ooc: {__OOC}
        short: {__SHORT}
        """)

    return args.file
    #__FILELIST = args.file


if __name__ == '__main__':

    # analyze command line arguments
    __FILELIST = __parse_args()


    # PART 1 - READ filenames and put them in a dictionary
    # read file-path(s) from STDIN

    for orig_filepath in __FILELIST:
        # ensure we only fetch jpg and jpeg and JPG and JPEG ...
        basename_and_path, extension = splitext_last(orig_filepath)
        if not extension in JPG_ORIG_EXTENSIONS:
            continue

        try:
            with PIL.Image.open(orig_filepath) as picture:
                timestamp, new_basename, date = create_new_basename(picture)

        except OSError:
            if not __QUIET:
                print(f"{orig_filepath} can't be opened as image", file=sys.stderr)
            continue

        if new_basename:
            duplicate = 0
            # There might be other jpg arround with the same timestamp
            # these might be either:
            # * serial shots (same camera same second) or
            # * parallel shots (other camera, same second)
            # * same camera after a clock reset
            # so we NEED to check first if this date is already claimed by an other shot
            # and save both (the second gets a number > 0 in duplicate

            while f"{timestamp}_{duplicate}" in PIC_DICT.keys():
                duplicate += 1

            # last changed time of that file to see for serial pictures which is the newest
            #ctime = str(os.path.getctime(orig_filepath))
            #mtime = str(os.path.getmtime(orig_filepath))


            orig_dirname, origfilename = os.path.split(orig_filepath)
            orig_basename, orig_all_extensions = splitext_all(origfilename)
            # the orig_dirname might be empty->absolute path
            orig_dirname = os.path.abspath(os.path.expanduser(orig_dirname))

            PIC_DICT[f"{timestamp}_{duplicate}"] = {
                'timestamp': timestamp,
                'duplicate': duplicate,
                'orig_basename' : orig_basename,
                'new_basename': new_basename,
                'orig_dirname' : orig_dirname,
                'orig_extension' : orig_all_extensions,
                'date': date,
                }

                #'ctime' : ctime,
                #'orig_filepath': orig_filepath,
            #print(PIC_DICT[f"{timestamp}_{duplicate}"] )

    # PART 2 - analyse what jpg files we've got and find accociate files

    PICLIST = sorted(PIC_DICT)

    # how long is my list? Is SERIAL_LENGTH long enough (do I have enough digits)?
    SERIAL_MIN_LENGTH = (len(str(len(PICLIST))))

    # also possible, but to import just for this an extra module?
    # is it faster? also on android?
    #import math
    #SERIAL_MIN_LENGTH=(int(math.log(len(PICLIST),10))+1)

    if SERIAL_MIN_LENGTH > SERIAL_LENGTH:
        SERIAL_LENGTH = SERIAL_MIN_LENGTH

    # SERIAL NUMBER included into the new picture name
    SERIAL = 0

    # walk now through all pictures to process them
    for pic in PICLIST:

        files_to_rename = [] # a list of filename tuples (old,new)
        SERIAL += 1

        orig_full_name = os.path.join(
            PIC_DICT[pic]['orig_dirname'],
            PIC_DICT[pic]['orig_basename'],
            ) + \
            PIC_DICT[pic]['orig_extension']


        date = PIC_DICT[pic]['timestamp']
        duplicate = PIC_DICT[pic]['duplicate']

        # TODO BETTER DUBLICATE HANDLING            pylint: disable=fixme
        # -> oldest file (mtime) should win "original without marker status"
        # -> check if the content seems to be really the same
        # -> real duplicates could be marked with a "DUPLICATE" string
        # current status is first come first serve

        picdict_set_serial_once(pic, SERIAL, SERIAL_LENGTH)

        orig_dirname, origfilename = os.path.split(orig_full_name)
        orig_basename, orig_all_extensions = splitext_all(origfilename)
        # the orig_dirname might be empty->absolute path
        orig_dirname = os.path.abspath(os.path.expanduser(orig_dirname))
        PIC_DICT[pic]['orig_dirname'] = orig_dirname
        PIC_DICT[pic]['orig_basename'] = orig_basename
        PIC_DICT[pic]['orig_extension'] = orig_all_extensions

        if __MAKEDATEDIR:
            __DATEDIR = PIC_DICT[pic]['date']

        if __DATEDIR:

            new_dirname = os.path.join(orig_dirname, __DATEDIR)

            # is this directory already there
            # is there something else what has this name but is no dir
            # write the dir
            # if problem, exit

            if not os.path.isdir(new_dirname):
                try:
                    if __SIMULATE:
                        if __VERBOSE:
                            print(f"INFO: create new directory: {new_dirname} (SIMULATION MODE)")
                    else:
                        if __VERBOSE:
                            print(f"INFO: create new directory: {new_dirname}")
                            os.makedirs(new_dirname)

                except FileExistsError:
                    print(f'ERROR: There is a {new_dirname}, but it is not a directory',
                          file=sys.stderr)
                    sys.exit()

        # don't use an other directory
        else:
            new_dirname = orig_dirname

        PIC_DICT[pic]['new_dirname'] = new_dirname

        if duplicate:
            PIC_DICT[pic]['new_basename'] = PIC_DICT[pic]['new_basename'] + f'_{duplicate}'

        if __OOC:
            PIC_DICT[pic]['new_extension'] = ".ooc" + JPG_EXTENSION
        else:
            PIC_DICT[pic]['new_extension'] = JPG_EXTENSION


        ## and now to the "extra" files which are accociated because of same basename

        extracounter = 0
        for extrafile in glob.glob(f'{orig_dirname}/{orig_basename}*'):
            if extrafile == orig_full_name:
                continue # next file

            # raw
            _, extension = splitext_last(extrafile)
            if extension in RAW_EXTENSIONS:
                extra = f"{pic}_raw"
                if duplicate:
                    # check if the first jpg (or a following) file
                    # already "claimed" this raw file
                    if picdict_has_orig_filepath(extrafile):
                        continue

                    # ok, we did look, nobody has this file so we keep it ...

                PIC_DICT[extra] = {
                    'orig_dirname' : orig_dirname,
                    'new_dirname' : new_dirname,
                    'orig_basename' : orig_basename,
                    'new_basename' : PIC_DICT[pic]['new_basename'],
                    'orig_extension' : extension,
                    'new_extension' : extension.lower(),
                    }
                    #'orig_filepath' : extrafile,


            else: # if not raw
                if picdict_has_orig_filepath(extrafile):
                    continue

                extra = f"{pic}_{extracounter}"
                _, extension = splitext_all(extrafile)
                PIC_DICT[extra] = {
                    'orig_dirname' : orig_dirname,
                    'new_dirname' : new_dirname,
                    'orig_extension' : extension,
                    'new_extension' : extension.lower(),
                    'orig_basename' : orig_basename,
                    'new_basename' : PIC_DICT[pic]['new_basename'],
                    }

                    #'orig_filepath' : extrafile,
                extracounter += 1


rename_files()

# don't forget how much mem is used - while developing
if "getmemsize" in dir():
    if __VERBOSE:
        print(f"Number of shots (max serial no.) {SERIAL}")
        print(f"Dictionary PIC_DICT entries:     {len(PIC_DICT)}")
        print("--- sizes of objects in bytes ----")
        print(f"Dictionary PIC_DICT:             {getmemsize(PIC_DICT)}")
        print(f"List PICLIST:                    {getmemsize(PICLIST)}")

# *** THE END ***
