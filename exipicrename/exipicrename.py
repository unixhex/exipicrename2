#!/usr/bin/env python3
"""
exipicrename

beta of python3 version.

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
import copy
import logging
# PIL from Pillow
import PIL
import PIL.Image
import PIL.ExifTags

version_info = (0, 0, 0, 8) # pylint: disable=invalid-name
version = '.'.join(str(digit) for digit in version_info) # pylint: disable=invalid-name

__CAMERADICT = {}       # how to rename certain camera names (load from csv)
__PIC_DICT = {}         # main storage for file meta data
__CONF = {
    'date_dir' : False,
    'verbose' : False,
    'debug' : False,
    'silent' : False,
    'dry_run' : False,
    'use_serial' : True,
    'use_duplicate' : True,
    'ooc' : False,
    'ooc_extension': '.ooc',
    'short_names' : False,
    'clean_data_after_run' : True,
    'serial_length': 3,
    'camera_rename_csv_file': os.path.join(os.path.dirname(__file__), "camera-model-rename.csv"),
    'zero_value_ersatz': 'x',
    'unwanted_character_ersatz': '-',
    'decimal_delimiter_ersatz': '-',
    'jpg_out_extension': '.jpg',
    'jpg_input_extensions': ('.jpg', '.JPG', '.jpeg', '.JPEG'),
    # source for raw_extensions: https://fileinfo.com/filetypes/camera_raw
    'raw_extensions': (
        '.orf', '.ORF', '.3fr', '.3FR',
        '.ari', '.ARI', '.arw', '.ARW',
        '.bay', '.BAY',
        '.cr2', '.CR2', '.cr3', '.CR3', '.crw', '.CRW',
        '.cs1', '.CS1', '.cxi', '.CXI',
        '.dcr', '.DCR', '.dng', '.DNG',
        '.eip', '.EIP', '.erf', '.ERF',
        '.fff', '.FFF',
        '.iiq', '.IIQ',
        '.j6i', '.J6I',
        '.k25', '.K25', '.kdc', '.KDC',
        '.mef', '.MEF', '.mfw', '.MFW', '.mos', '.MOS', '.mrw', '.MRW',
        '.nef', '.NEF', '.nrw', '.NRW',
        '.pef', '.PEF',
        '.raf', '.RAF', '.raw', '.RAW', '.rw2', '.RW2',
        '.rwl', '.RWL', '.rwz', '.RWZ',
        '.sr2', '.SR2', '.srf', '.SRF', '.srw', '.SRW',
        '.x3f', '.X3F',
    )
}


def set_raw_extensions(ext_set: set):
    """this set of extension we use to recognize raw files
    (please don't forget the delimiter)
    HINT: use only if neccessary, the default is rather inclusive
    """
    __CONF['raw_extensions'] = ext_set
def get_raw_extensions():
    """get set of extension to recognize input raw files
    (should include the delimiter (.)"""
    return __CONF['raw_extensions']

def set_jpg_input_extensions(ext_set: set):
    """this set of extension we use to recognize JPEG files
    (please don't forget the delimiter)"""
    __CONF['jpg_input_extensions'] = ext_set
def get_jpg_input_extensions():
    """get set of extension to recognize input JGEG files
    (should include the delimiter (.)"""
    return __CONF['jpg_input_extensions']

def set_jpg_out_extension(ext: str = ".jpg"):
    """this extension we use as output for JPEG files
    please don't forget the delimiter (.)"""
    __CONF['jpg_out_extension'] = ext
def get_jpg_out_extension():
    """get extension for output JGEG files
    (should include the delimiter (.)"""
    return __CONF['jpg_out_extension']

def set_ooc_extension(ext: str = ".jpg"):
    """additional extension to mark 'out of cam' pictures
    comes before the jpg_out_extension
    please don't forget the delimiter (.)"""
    # we don't trust commandline-arguments, so we clean it ...
    newext = re.sub(r'[^a-zA-Z0-9._-]+', '', ext.strip().lower())
    __CONF['ooc_extension'] = newext
def get_ooc_extension():
    """additional extension to mark 'out of cam' pictures
    comes before the jpg_out_extension
    (should include the delimiter (.)"""
    return __CONF['ooc_extension']

def set_decimal_delimiter_ersatz(dds: str):
    """which symbol should be used instead
    of the decimal delimiter '.'
    e.g. for aperture (blende)
    (since a dot is not good in file names we use something else)"""
    __CONF['decimal_delimiter_ersatz'] = dds
def get_decimal_delimiter_ersatz():
    """return substitution string for decimal delimiter"""
    return __CONF['decimal_delimiter_ersatz']

def set_unwanted_character_ersatz(ucs: str):
    """if the lens is analog, the value for aperture or length might be zero
    which string should be written instead?"""
    __CONF['unwanted_character_ersatz'] = ucs
def get_unwanted_character_ersatz():
    """return substitution string for zero aperture or length values"""
    return __CONF['unwanted_character_ersatz']

def set_zero_value_ersatz(zvs: str):
    """if the lens is analog, the value for aperture or length might be zero
    which string should be written instead?"""
    __CONF['zero_value_ersatz'] = zvs
def get_zero_value_ersatz():
    """return substitution string for zero aperture or length values"""
    return __CONF['zero_value_ersatz']

def set_camera_rename_csv_name(filename: str):
    """set name for the 'camera-name-translation'"""
    __CONF['camera_rename_csv_file'] = filename
def get_camera_rename_csv_name():
    """get name for the 'camera-name-translation'"""
    return __CONF['camera_rename_csv_file']

def set_serial_length(serial_length: int = 3):
    """set the length of the serial number (to be included in the file name) """
    __CONF['serial_length'] = serial_length
def get_serial_length():
    """get the length of the serial number (to be included in the file name) """
    return __CONF['serial_length']

def set_clean_data_after_run(__clean: bool = True):
    """for tests we wan't to analyze the dict,
    but if used as a module, it needs to be cleaned up"""
    __CONF['clean_data_after_run'] = __clean
def do_clean_data_after_run():
    """for tests we wan't to analyze the dict,
    but if used as a module, it needs to be cleaned up"""
    return __CONF['clean_data_after_run']

def set_use_date_dir(_use_date_dir: bool = True):
    """write files to separate directory?"""
    __CONF['date_dir'] = _use_date_dir
def use_date_dir():
    """write files to separate directory?"""
    return __CONF['date_dir']

def set_verbose(verbose: bool = True):
    """set verbosity (bool)"""
    __CONF['verbose'] = verbose
def is_verbose():
    """get verbosity (bool)"""
    return __CONF['verbose']

def set_debug(debug: bool = True):
    """set debug (bool)"""
    __CONF['debug'] = debug
def is_debug():
    """get debug status (bool)"""
    return __CONF['debug']

def set_silent(silent: bool = True):
    """set silence (bool)"""
    __CONF['silent'] = silent
def is_silent():
    """get silence (bool)"""
    return __CONF['silent']

def set_dry_run(dry_run: bool = True):
    """set dry-run (simulation-mode status)"""
    __CONF['dry_run'] = dry_run
def is_dry_run():
    """get dry-run (simulation-mode status)"""
    return __CONF['dry_run']

def set_use_serial(use_serial: bool = True):
    """include a serial number"""
    __CONF['use_serial'] = use_serial
def use_serial():
    """should we include serial number?"""
    return __CONF['use_serial']

def set_use_duplicate(use_duplicate: bool = True):
    """include a duplicate number if the same timestamp occurs"""
    __CONF['use_duplicate'] = use_duplicate
def use_duplicate():
    """should we include a duplicate number?"""
    return __CONF['use_duplicate']

def set_use_ooc(_use_ooc: bool = True):
    """set use of ooc extension"""
    __CONF['ooc'] = _use_ooc
def use_ooc():
    """get use of ooc extension"""
    return __CONF['ooc']

def set_short_names(short_names: bool = True):
    """use short names (without camera exif)"""
    __CONF['short_names'] = short_names
def use_short_names():
    """get usage of short names (without camera exif)"""
    return __CONF['short_names']

def export_pic_dict():
    """for tests"""
    return copy.deepcopy(__PIC_DICT)


def verboseprint(*msg):
    """print verbose messages"""
    #print("P", *msg)
    #logging.info(*msg)
    for m in msg:
        logging.info(str(m))

def errorprint(*args):
    """print error messages"""
    #print(*args, file=sys.stderr)
    for m in args:
        logging.error(str(m))

def __create_new_basename(img):
    """create a new filename based on exif data"""
    # fetch tagging from https://stackoverflow.com/a/4765242
    try:
        exif = {
            PIL.ExifTags.TAGS[k]: v
            for k, v in img._getexif().items() # pylint: disable=protected-access
            if k in PIL.ExifTags.TAGS
        }
    except AttributeError:
        if is_verbose():
            errorprint('NO exif info in ' + img.filename)
        return None, None, None

    try:
        _datetime = format_datetime(exif['DateTimeOriginal'])
        _date = format_date(exif['DateTimeOriginal'])
        if not use_short_names():
            _aperture = __format_aperture_tuple(exif['FNumber'])
            _exposure_time = __format_exposuretime_tuple(exif['ExposureTime'])
            _focal_len = __format_focal_length_tuple(exif['FocalLength'])
            _camera = __format_camera_name(exif['Model'])
            _iso = (exif['ISOSpeedRatings'])
    except KeyError as err:
        if is_verbose():
            errorprint('(Some) exif tags missing in ' + img.filename, err)
        return None, None, None

    if not use_short_names():
        _new_basename = f"{_datetime}{{}}__{_camera}__{_focal_len}" + \
            f"__{_aperture}__t{_exposure_time}__iso{_iso}"
    else:
        _new_basename = f"{_datetime}{{}}"

    return _datetime, _new_basename, _date

def __format_camera_name(_name):
    """format camera name - substitute unwanted characters, lower case
    if available, read translations for camera models from csv and apply them """
    _newname = re.sub(r'[^a-zA-Z0-9]+', get_unwanted_character_ersatz(), _name.strip().lower())
    __read_camera_rename_csv()

    if _newname in __CAMERADICT:
        return __CAMERADICT[_newname]

    return _newname


def __format_aperture_tuple(_ap):
    """format aperture tuple to short printable string
    new pillow might not return tuple, so check first"""

    if (isinstance(_ap,tuple)):
        numerator = _ap[0]  # numerator = zaehler
        divisor = _ap[1]    # divisor = nenner
    else:
        numerator=_ap.numerator
        divisor=_ap.denominator

    if numerator == 0:
        return get_zero_value_ersatz()
    if numerator % divisor == 0:
        return "f" + str(numerator//divisor)
    else:
        return "f" + str(numerator/divisor).replace('.', get_decimal_delimiter_ersatz())

def __format_focal_length_tuple(_tuple):
    """format FocalLenght tuple to short printable string
    we ignore the position after the decimal point
    because it is usually not very essential for focal length
    """
    if (isinstance(_tuple,tuple)):
        numerator = _tuple[0]
        divisor = _tuple[1]
    else:
        numerator=_tuple.numerator
        divisor=_tuple.denominator

    if numerator == 0:
        return get_zero_value_ersatz()

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


def __format_exposuretime_tuple(_time):
    """format ExposureTime tuple to short printable string
    fractions over or equal 1 second are marked with s, e.g. 8s
    fractions below 1 second are broken down to the divisor,
    this is a bit incorrect but short and common e.g. in cameras
    (and we want to have a short string)
    """
    if (isinstance(_time,tuple)):
        numerator = _time[0]
        divisor = _time[1]
    else:
        numerator=_time.numerator
        divisor=_time.denominator
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


def __read_camera_rename_csv():
    """read the model translate csv - if available (only once)"""
    if __CAMERADICT:
        # we've read the csv already
        return
    try:
        with open(get_camera_rename_csv_name()) as csvfile:
            camera_model_translate = csv.reader(csvfile, delimiter=',')
            for row in camera_model_translate:
                __CAMERADICT[row[0]] = row[1]
    except OSError:
        if is_verbose():
            verboseprint("camera translation csv not found: ", get_camera_rename_csv_name())
        pass

def splitext_all(_filename):
    """split all extensions (after the first .) from the filename
    should work similar to os.path.splitext (but that splits only the last extension)
    """
    _name, _extensions = _filename.split('.')[0], '.'.join(_filename.split('.')[1:])
    return(_name, "."+ _extensions)


def __picdict_set_serial_once(_pic, _serial, _serial_length):
    """set serial number in a global __PIC_DICT dictionary entry (if not set yet or if empty)"""
    # make a string out of "_serial", fill it up with 0 up to _serial_length
    # include it into the new file base name
    try:
        _ = __PIC_DICT[_pic]['serial']
        return False
    except KeyError:
        pass

    __PIC_DICT[_pic]['serial'] = _serial
    if use_serial():
        __PIC_DICT[_pic]['new_basename'] = \
            __PIC_DICT[_pic]['new_basename'].format("__" +str(_serial).zfill(_serial_length))
    else:
        __PIC_DICT[_pic]['new_basename'] = \
            __PIC_DICT[_pic]['new_basename'].format("")
    return True

def __picdict_has_orig_filepath(filepath):
    """search if this filename is already recorded in global __PIC_DICT"""

    _dir, _ = os.path.split(filepath)
    _basename, _ext = os.path.splitext(_)

    for filerecord in __PIC_DICT.values():
        try:
            if filerecord['orig_basename'] == _basename \
                and filerecord['orig_extension'] == _ext \
                and filerecord['orig_dirname'] == _dir:
                return True
        except KeyError:
            pass
        return False

def __rename_files():
    """rename files (after check if we don't overwrite)"""
    for k in sorted(__PIC_DICT):

        oldname = "{}/{}{}".format(
            __PIC_DICT[k]["orig_dirname"],
            __PIC_DICT[k]["orig_basename"],
            __PIC_DICT[k]["orig_extension"],
            )

        newname = "{}/{}{}".format(
            __PIC_DICT[k]["new_dirname"],
            __PIC_DICT[k]["new_basename"],
            __PIC_DICT[k]["new_extension"],
            )

        if oldname == newname:
            continue

        if not os.path.isfile(oldname) and not is_silent():
            errorprint(f"WARNING: want to rename {oldname}\n"
                  f"                     to {newname}\n"
                  f"         but orig file not available any more")
            continue
        if os.path.isfile(newname) and not is_silent():
            errorprint(f"WARNING: did not overwrite existing file\n"
                  f"\t{newname}\n\twith:\n \t{oldname}")
            continue
            sys.exit()  # pylint: disable=unreachable
            # we really really don't want to overwrite files

        if is_verbose():
            msg = ""
        if is_dry_run():
            msg = "SIMULATION| "
        if is_verbose() or (is_dry_run() and not is_silent()):
            verboseprint(f"{msg}rename old: {oldname} ")
            verboseprint(f"{msg}to NEW    : {newname} ")

        if not is_dry_run():
            os.rename(oldname, newname)


def __parse_args():
    "read and interpret commandline arguments with argparse"

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        )
    parser.add_argument("file", nargs='+',
                        help="jpeg files to rename")
    parser.add_argument("-d", "--datedir", action="store_true",
                        help="sort and store pictures to sub-directories"
                        "depending on DateTimeOriginal (YYYY-MM-DD)")
    parser.add_argument("-o", "--ooc", action="store_true",
                        help="use .ooc.jpg as filename extension (for Out Of Cam pictures)")
    parser.add_argument("--oocstring", action="store",
                        help="use string as additional extension,"
                        " don't forget the '.' as delimiter")
    parser.add_argument("-s", "--short", "--short-names",
                        action="store_true",
                        help="use short names: only date + serial number, "
                        "no exhaustive camera data")
    parser.add_argument("-n", "--simulate", "--dry-run",
                        action="store_true",
                        help="don't rename, just show what would happen")
    parser.add_argument("--debug",
                        action="store_true",
                        help="debug")
    parser.add_argument('-V', '--version',
                        action='version',
                        version=f'%(prog)s {version}',
                        help='show the version number and exit')
    group_number = parser.add_mutually_exclusive_group()
    group_number.add_argument("--no-serial", action="store_true",
                        help="don't include a serial number")
    group_number.add_argument("--no-duplicate", action="store_true",
                        help="don't attach a duplicate number if the same timestamp occurrs more than once")
    group_verbose = parser.add_mutually_exclusive_group()
    group_verbose.add_argument("-v", "--verbose", action="store_true")
    group_verbose.add_argument("-q", "--quiet", "--silent", action="store_true")
    args = parser.parse_args()
    if args.no_serial:
        set_use_serial(False)
        set_use_duplicate(True)
    if args.no_duplicate:
        set_use_serial(True)
        set_use_duplicate(False)
    if args.quiet:
        set_silent(True)
        set_verbose(False)
    if args.datedir:
        set_use_date_dir(True)
    if args.simulate:
        set_dry_run(True)
    if args.ooc:
        set_use_ooc(True)
    if args.oocstring:
        set_ooc_extension(args.oocstring)
        set_use_ooc(True)
    if args.short:
        set_short_names(True)
    if args.debug:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
        set_debug(True)
    if args.verbose:
        if logging.getLogger().getEffectiveLevel() >= logging.INFO:
            logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
        set_verbose(True)
        verboseprint(f"""
        version: {version}
        FLAGS:
        verbose: {is_verbose()}
        silent: {is_silent()}
        dry_run: {is_dry_run()}
        use_date_dir: {use_date_dir()},
        use_ooc: {use_ooc()}
        short_names: {use_short_names()}
        use_serial: {use_serial()}
        use_duplicate: {use_duplicate()}
        log_level: {logging.getLevelName(logging.getLogger().getEffectiveLevel())}
        """)
    if logging.getLogger().getEffectiveLevel() >= logging.INFO:
        logging.basicConfig(format='%(levelname)s:%(message)s')
    return args.file


def __read_picture_data(_filelist):
    """ READ picture exif data, put it in dictionary __PIC_DICT"""

    for orig_filepath in _filelist:
        # ensure we only fetch jpg and jpeg and JPG and JPEG ...
        _, extension = splitext_last(orig_filepath)
        if not extension in get_jpg_input_extensions():
            continue

        orig_dirname, origfilename = os.path.split(orig_filepath)
        orig_basename, orig_all_extensions = splitext_all(origfilename)
        # the orig_dirname might be empty->absolute path
        orig_dirname = os.path.abspath(os.path.expanduser(orig_dirname))
        orig_filepath = os.path.join(orig_dirname, orig_basename + orig_all_extensions)

        # ensure we don't read the same picture twice

        if __picdict_has_orig_filepath(orig_filepath):
            if is_verbose():
                verboseprint(f"{orig_filepath} already processed")
            continue

        try:
            with PIL.Image.open(orig_filepath) as picture:
                timestamp, new_basename, date = __create_new_basename(picture)

        except OSError:
            if not is_silent():
                errorprint(f"{orig_filepath} can't be opened as image")
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

            while f"{timestamp}_{duplicate}" in __PIC_DICT.keys():
                duplicate += 1

            # last changed time of that file to see for serial pictures which is the newest
            #ctime = str(os.path.getctime(orig_filepath))
            #mtime = str(os.path.getmtime(orig_filepath))


            __PIC_DICT[f"{timestamp}_{duplicate}"] = {
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


def __organize_picture_data():
    """analyse what jpg files we've got and find accociate files"""

    pic_list = sorted(__PIC_DICT)

    # how long is my list? Is the default serial length long enough (do I have enough digits)?
    serial_min_length = (len(str(len(pic_list))))

    if serial_min_length > get_serial_length():
        set_serial_length(serial_min_length)

    # first serial NUMBER to be included into the new picture name
    serial = 1

    # walk now through all pictures to process them
    for pic in pic_list:
        orig_extension = __PIC_DICT[pic]['orig_extension']
        extension = "." + orig_extension.split(".")[-1]

        if extension in get_jpg_input_extensions():
            __organize_jpg_files(pic, serial)
            __organize_extra_files(pic)
            serial += 1

def __organize_jpg_files(pic, serial):
    """organize new paths for the jpg files"""
    orig_full_name = os.path.join(
        __PIC_DICT[pic]['orig_dirname'],
        __PIC_DICT[pic]['orig_basename'],
        ) + \
        __PIC_DICT[pic]['orig_extension']

    duplicate = __PIC_DICT[pic]['duplicate']

    # TODO BETTER DUBLICATE HANDLING            pylint: disable=fixme
    # -> oldest file (mtime) should win "original without marker status"
    # -> check if the content seems to be really the same
    # -> real duplicates could be marked with a "DUPLICATE" string
    # current status is first come first serve

    __picdict_set_serial_once(pic, serial, get_serial_length())

    orig_dirname, origfilename = os.path.split(orig_full_name)
    orig_basename, orig_all_extensions = splitext_all(origfilename)
    # the orig_dirname might be empty->expand to absolute path
    orig_dirname = os.path.abspath(os.path.expanduser(orig_dirname))
    __PIC_DICT[pic]['orig_dirname'] = orig_dirname
    __PIC_DICT[pic]['orig_basename'] = orig_basename
    __PIC_DICT[pic]['orig_extension'] = orig_all_extensions

    # move files to other directory
    if use_date_dir():

        new_dirname = os.path.join(orig_dirname, __PIC_DICT[pic]['date'])

        # is this directory already there
        # is there something else what has this name but is no dir
        # write the dir
        # if problem, exit

        if not os.path.isdir(new_dirname):
            try:
                if is_dry_run():
                    if is_verbose():
                        verboseprint(f"INFO: create new directory: {new_dirname} (SIMULATION MODE)")
                else:
                    if is_verbose():
                        verboseprint(f"INFO: create new directory: {new_dirname}")

                    os.makedirs(new_dirname)

            except FileExistsError:
                errorprint(f'ERROR: There is a {new_dirname}, but it is not a directory')
                sys.exit()

    # don't move files to an other directory
    else:
        new_dirname = orig_dirname

    __PIC_DICT[pic]['new_dirname'] = new_dirname

    if duplicate and use_duplicate():
        __PIC_DICT[pic]['new_basename'] = __PIC_DICT[pic]['new_basename'] + f'_{duplicate}'

    if use_ooc():
        __PIC_DICT[pic]['new_extension'] = get_ooc_extension() + get_jpg_out_extension()
    else:
        __PIC_DICT[pic]['new_extension'] = get_jpg_out_extension()


def __organize_extra_files(pic):
    """organize new paths for the associated files"""
    extracounter = 0

    orig_dirname = __PIC_DICT[pic]['orig_dirname']
    new_dirname = __PIC_DICT[pic]['new_dirname']
    orig_basename = __PIC_DICT[pic]['orig_basename']
    orig_full_name = os.path.join(
        __PIC_DICT[pic]['orig_dirname'],
        __PIC_DICT[pic]['orig_basename'],
        ) + \
        __PIC_DICT[pic]['orig_extension']

    duplicate = __PIC_DICT[pic]['duplicate']

    for extrafile in glob.glob(f'{orig_dirname}/{orig_basename}.*'):
        if extrafile == orig_full_name or os.path.isdir(extrafile):
            continue # next file

        # raw
        _, extension = splitext_last(extrafile)
        if extension in get_raw_extensions():
            extra = f"{pic}_raw"
            if duplicate:
                # check if the first jpg (or a following) file
                # already "claimed" this raw file
                if __picdict_has_orig_filepath(extrafile):
                    continue

                # ok, we did look, nobody has this file so we keep it ...

        else: # if not raw
            if __picdict_has_orig_filepath(extrafile):
                continue

            extra = f"{pic}_{extracounter}"
            _, extension = splitext_all(extrafile)

        __PIC_DICT[extra] = {
            'orig_dirname' : orig_dirname,
            'new_dirname' : new_dirname,
            'orig_basename' : orig_basename,
            'new_basename' : __PIC_DICT[pic]['new_basename'],
            'orig_extension' : extension,
            'new_extension' : extension.lower(),
            }

        if extension not in get_raw_extensions():
            extracounter += 1

def clean_stored_data():
    """cleanup stored data"""
    global __PIC_DICT  # pylint: disable=global-statement
    __PIC_DICT = {}

def exipicrename(filelist):
    """Read exif data from (filelist) pictures,
    rename them and associated files (e.g. raw files, xmp files, ... ).
    input should be a list of filenames (one single filenames as string is also accepted)"""
    # read exif data from picture files and store this data in __PIC_DICT

    # for single files we don't require a list
    if not isinstance(filelist, list):
        if isinstance(filelist, str):
            filelist = [filelist]
        else:
            if not is_silent():
                errorprint(f"Error: expected list of files ")
            sys.exit(1)

    __read_picture_data(filelist)

    # analyse what jpg files we've got and find accociate files
    # write all to __PIC_DICT
    __organize_picture_data()

    # now do the renaming (based on all stored data in __PIC_DICT)
    __rename_files()

    # for use as a module: clean up stored data from __PIC_DICT
    if do_clean_data_after_run():
        clean_stored_data()

def main():
    """main - entry point for command line call"""
    #logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    #logging.basicConfig(format='%(levelname)s:%(message)s')
    exipicrename(__parse_args())

if __name__ == '__main__':
    main()


# *** THE END ***
