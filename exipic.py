#!/usr/bin/env python3
"""
exipicrename

reads exif data from pictures
(and later on renames these pictures)

version 2 - except bash with exiftool now with python3 and pillow

status: testing Pillow / early development
"""
# pylint: disable=W0511    # don't warn for TODO , I know it is not finished, yet

import os
from os.path import splitext as splitext_last
import sys
import re
import csv
import time
import glob
from collections import defaultdict
# PIL from Pillow
import PIL
import PIL.Image
import PIL.ExifTags

try:
    from pysize import get_size as getmemsize #FIXME just for debugging
    # pysize from https://github.com/bosswissam/pysize
except:
    pass    

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

# we include a serial number into the filename. This is the default length, if neccessary that
# number gets more digits (depending how much files are renamed on that run).
SERIAL_LENGTH = 3

MODEL_TRANSLATE_CSV = "camera-model-rename.csv"
CAMERADICT = {}
PICDICT = {}

PICDICT2 = defaultdict(list)

ALL_FILES_TO_RENAME = []

# this extensions we read as JPEG
JPG_ORIG_EXTENSIONS = ('.jpg', '.JPG', '.jpeg', '.JPEG')

# this extension we use as output JPEG extension
JPG_EXTENSION='.jpg'


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



def create_new_filename(img):
    """create a new filename based on exif data"""
    # fetch tagging from https://stackoverflow.com/a/4765242
    try:
        exif = {
            PIL.ExifTags.TAGS[k]: v
            for k, v in img._getexif().items() # pylint: disable=protected-access
            if k in PIL.ExifTags.TAGS
        }
    except AttributeError:
        #print (f"image has no exif tags")
        return None, None

    # TODO better exception handling if exif-values are missing

    _aperture = format_aperture(exif['FNumber'])
    _exposure_time = format_exposuretime_tuple(exif['ExposureTime'])
    _focal_len = format_focal_length_tuple(exif['FocalLength'])
    _camera = format_camera_name(exif['Model'])
    _datetime = format_time(exif['DateTimeOriginal'])
    _iso = (exif['ISOSpeedRatings'])

#    print(f"date+time: {_datetime}\n"
#          f"camera: {_camera}\n"
#          f"Focal Length: {_focal_len}\n"
#          f"Exposure Time: {_exposure_time}\n"
#          f"Aperture: {_aperture}\n"
#          f"ISO: {_iso}\n"
#          )

    #print(f"{_datetime}__000__{_camera}__{_focal_len}__{_aperture}__iso{_iso}.jpg")
    return _datetime, (f"{_datetime}__{{}}__{_camera}__{_focal_len}__{_aperture}__iso{_iso}")
    #return True

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


def format_time(_datetime):
    """format time string"""
    _time_struct = time.strptime(_datetime, "%Y:%m:%d %H:%M:%S")
    return time.strftime("%Y%m%d_%H%M%S", _time_struct)


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
    return(_name, _extensions)

def debug_print_rename_list():
    """DEBUG print tuples which will be the input for the big renaming"""
    for file_tuple in ALL_FILES_TO_RENAME:
        print("old:" + file_tuple[0])
        print("NEW:" + file_tuple[1])


if __name__ == '__main__':

    # PART 1 - READ filenames and put them in a dictionary
    # read file-path(s) from STDIN
    for orig_picturepath in sys.argv[1:]:

        # ensure we only fetch jpg and jpeg and JPG and JPEG ...
        #basename_and_path, extension = os.path.splitext(orig_picturepath)
        basename_and_path, extension = splitext_last(orig_picturepath)
        if not extension in JPG_ORIG_EXTENSIONS:
            #print(f"{orig_picturepath} has the wrong extension for a JPG picture") # TODO VERBOSE
            continue

        try:
            with PIL.Image.open(orig_picturepath) as picture:
                timestamp, new_picturepath = create_new_filename(picture)

        except OSError:
            print(f"{orig_picturepath} can't be opened as image") # TODO VERBOSE
            continue

        if new_picturepath:
            duplicate = 0
            # There might be other jpg arround with the same timestamp
            # these might be either:
            # * serial shots (same camera same second) or 
            # * parallel shots (other camera, same second)
            # * same camera after a clock reset
            # so we NEED to check first if this date is already claimed by an other shot
            # and save both (the second gets a number > 0 in duplicate

            while (f"{timestamp}_{duplicate}" in PICDICT.keys()):
                #print(f"{timestamp}_{duplicate} ##################") # TODO VERBOSE
                duplicate += 1
           
            # last changed time of that file to see for serial pictures which is the newest
            ctime=str(os.path.getctime(orig_picturepath))
            mtime=str(os.path.getmtime(orig_picturepath))

            #print(f"{timestamp}_{duplicate} #<<<<<<<<<<<<<<<<<<<<####") # TODO VERBOSE
            PICDICT[f"{timestamp}_{duplicate}"] = {
                        'timestamp': timestamp, 
                        'duplicate': duplicate,
                        'orig_picturepath': orig_picturepath,
                        'new_picturepath_no_serial': new_picturepath,
                        'ctime' : ctime,
                        'do_rename' : False,
                        }
###            PICDICT2[timestamp].append({
###                        'timestamp': timestamp, 
###                        #'duplicate': duplicate,
###                        'orig_picturepath': orig_picturepath,
###                        #'new_picturepath_no_serial': new_picturepath,
###                        'ctime' : ctime,
###                        'mtime' : mtime,
###                        #'do_rename' : False,
###                       })

###    print (PICDICT)
###    print (PICDICT2)
###    print ("-------------")
###    for key in PICDICT2.keys():
###        print (key)
###        print (len(PICDICT2[key]))
###        for Z in PICDICT2[key]:
###            print(Z)
###        print ("...")


    # PART 2 - analyse what jpg files we've got and find accociate files
    PICLIST = list(PICDICT.keys())

    # how long is my list? Is SERIAL_LENGTH long enough (do I have enough digits)?
    SERIAL_MIN_LENGTH = (len(str(len(PICLIST))))

    # also possible, but to import just for this an extra module?
    # is it faster? also on android?
    #import math
    #SERIAL_MIN_LENGTH=(int(math.log(len(PICLIST),10))+1)

    if SERIAL_MIN_LENGTH > SERIAL_LENGTH:
        SERIAL_LENGTH = SERIAL_MIN_LENGTH

    # PICLIST contains timestamp + duplicate integer,
    # sort it, we want to have our serials in correct sequence
    PICLIST.sort()

    # SERIAL NUMBER included into the new picture name
    SERIAL = 0

    # walk now through all pictures to process them
    for pic in PICLIST:

        files_to_rename = [] # a list of filename tuples (old,new)
        SERIAL += 1
###PICDICT
###picdictkey - timestamp+duplicatecounter
###  timestamp  <- on init
###  duplicate  <- on init
###  orig_picturepath <- on init (name with path and extension)
###  new_picturepath_no_serial <- on init (name with path, extension and template {} for serial)
###  serial
###  origbasename   . 
###  origallextensions  . 
###  orig_dirname .
###  orig_rawpath
###  new_basename .
###  newextension -> jpg    # DO I NEED THIS or is it enough to have as constant?
###  newdir (if requested)
###  newrawname
###  associated_list list of set (origassociated files|newassociated files)
###  do_rename (bool)

        origname = PICDICT[pic]['orig_picturepath']
        date = PICDICT[pic]['timestamp']
        duplicate = PICDICT[pic]['duplicate']

        # TODO BETTER DUBLICATE HANDLING
        # -> oldest file (mtime) should win "original without marker status"
        # -> check if the content seems to be really the same
        # -> real duplicates could be marked with a "DUPLICATE" string
        # FIXME: current status is first come first serve

        # make a string out of "SERIAL", fill it up with 0 up to SERIAL_LENGTH
        # include it into the new file base name
        new_basename = PICDICT[pic]['new_picturepath_no_serial'].format(str(SERIAL).zfill(SERIAL_LENGTH))

        orig_dirname, origfilename = os.path.split(origname)
        origbasename, origallextensions = splitext_all(origfilename)

        PICDICT[pic]['orig_dirname'] = orig_dirname
        PICDICT[pic]['origbasename'] = origbasename
        PICDICT[pic]['origallextensions'] = origallextensions
        PICDICT[pic]['serial'] = SERIAL
        ### PICDICT[pic]['newextension'] = JPG_EXTENSION

        if not duplicate:
            PICDICT[pic]['new_basename'] = new_basename + JPG_EXTENSION
        else:
            PICDICT[pic]['new_basename'] = new_basename + f'_{duplicate}' + JPG_EXTENSION

        # FIXME: REMOVE 
        files_to_rename.append(
            (f'{origname}', f'{orig_dirname}/{new_basename}.{origallextensions.lower()}'))

        # identify associated raw and xml files
        for extrafile in glob.glob(f'{orig_dirname}/{origbasename}*'):
            if extrafile == origname:
                continue
            # print(">>", extrafile)  # TODO DEBUG
            # raw
            _, extension = splitext_last(extrafile)
            if extension in RAW_EXTENSIONS:
                if duplicate:
                    first_timestamp = timestamp + "_0"
                    # check if the first file already claimed this raw file
                    print (f"""
                    # {PICDICT[pic]['orig_picturepath']} ####
                    # {PICDICT[pic]['ctime']} ####
                    = {pic} {duplicate}
                    a {extrafile}
                    """)
                    try:
                        if extrafile == PICDICT[f'{timestamp}_0']['orig_rawpath']:
                            print(f"DOUBLE READ: {extrafile} ~~~~~~~~~")
                            #sys.exit()
                    except KeyError:
                        pass
                else:
                    PICDICT[pic]['orig_rawpath'] = extrafile
                    print (f"""
                    * {PICDICT[pic]['orig_picturepath']} ****
                    * {PICDICT[pic]['ctime']} ****
                    = {pic} {duplicate}
                    a {extrafile}
                    """)
                    files_to_rename.append(
                        (f'{extrafile}', f'{orig_dirname}/{new_basename}{extension.lower()}'))

            else:
            # TODO FIXME: other assocciated files might be claimed by more than one jpg
            # if duplicate > 0, this should not be announced
                printme=True 
                for knownfile,_ in files_to_rename:
                    if extrafile == knownfile:
                        print ("HAB ICH DOCH SCHON")
                        printme=False

                if printme:
                    _, extension = splitext_all(extrafile)
                    files_to_rename.append(
                        (f'{extrafile}', f'{orig_dirname}/{new_basename}.{extension.lower()}'))
                



        # TODO check if target name already given
        # TODO rename

        ALL_FILES_TO_RENAME.extend(files_to_rename)

debug_print_rename_list()

# don't forget how much mem is used - while developing
if "getmemsize" in dir():
    print("sizes of objects in byte:")
    print(f"Tuple-List ALL_FILES TO RENAME: {getmemsize(ALL_FILES_TO_RENAME)}")
    print(f"Dictionary PICDICT:             {getmemsize(PICDICT)}")

# *** THE END ***
