#!/usr/bin/env python3

"""unittest for exipicrename"""
import unittest
import os
import sys
from tempfile import TemporaryDirectory
from shutil import copy
# my test subject lives one dir up
sys.path.append(os.path.join(os.path.dirname(__file__),".."))
import exipicrename

#VERBOSE = True
VERBOSE = False

class TestExipicrenameVirtual(unittest.TestCase):
    """unittest class for exipicrename (virtual - without file changes)"""

    test_dir, _ = os.path.split(os.path.abspath(__file__))

    testfiles = [
        test_dir + '/fixtures/x_test.jpg',  # e520
        test_dir + '/fixtures/x_test.jpg',  # same file e520
        test_dir + '/fixtures/y_test.jpg',  # s4mini
        test_dir + '/fixtures/yy_test.jpg', # duplicate
        test_dir + '/fixtures/z_test.jpg',  # empty
        test_dir + '/fixtures/0_test.jpg',  # file not existing
        ]

    TEST_DICT_DEFAULT = {
        '20090604_184453_0': {
            'timestamp': '20090604_184453',
            'duplicate': 0,
            'orig_basename': 'x_test',
            'new_basename': '20090604_184453__001__e-520__25mm__f2-8__t3200__iso100',
            #'orig_dirname': 'absolut path, not usefull for tests'
            'orig_extension': '.jpg',
            'date': '2009-06-04',
            'serial': 1,
            #'new_dirname':
            'new_extension': '.jpg'
            },
        '20090604_184453_0_0': {
            #'orig_dirname': 'absolut path, not usefull for tests',
            #'new_dirname': 'absolut path, not usefull for tests',
            'orig_basename': 'x_test',
            'new_basename': '20090604_184453__001__e-520__25mm__f2-8__t3200__iso100',
            'orig_extension': '.xml',
            'new_extension': '.xml'},
        '20090604_184453_0_raw': {
            #'orig_dirname': 'absolut path, not usefull for tests',
            #'new_dirname': 'absolut path, not usefull for tests',
            'orig_basename': 'x_test',
            'new_basename': '20090604_184453__001__e-520__25mm__f2-8__t3200__iso100',
            'orig_extension': '.orf',
            'new_extension': '.orf'
            }
        }
    TEST_FIRST_KEY = '20090604_184453_0'
    TEST_SHORT_BASENAME = '20090604_184453__001'

    def test_dry_run_false(self):
        """test without option --dry-run (virtual)"""
        exipicrename.set_dry_run(False)
        self.assertFalse(exipicrename.is_dry_run(), f"dry run should be set to False")
    def test_dry_run_true(self):
        """test option --dry-run (virtual)"""
        exipicrename.set_dry_run(True)
        self.assertTrue(exipicrename.is_dry_run(), f"dry run should be set to True")

    def test_rename_default(self):
        """test default renaming (virtual)"""
        exipicrename.set_dry_run(True)
        if VERBOSE:
            exipicrename.set_verbose(True)
        else:
            exipicrename.set_silent(True)
        exipicrename.set_short_names(False)
        exipicrename.set_use_ooc(False)
        exipicrename.set_clean_data_after_run(False)
        exipicrename.exipicrename(self.testfiles)
        e_dict = exipicrename.export_pic_dict()

        for index in self.TEST_DICT_DEFAULT:
            self.assertEqual(
                self.TEST_DICT_DEFAULT[index]['new_basename'],
                e_dict[index]['new_basename'],
                f"renaming problem\ndictionary: >{e_dict}<")
            self.assertEqual(
                self.TEST_DICT_DEFAULT[index]['new_extension'],
                e_dict[index]['new_extension'],
                f"renaming problem\ndictionary: >{e_dict}<")

        exipicrename.clean_stored_data()

    def test_rename_short_names(self):
        """test option --short (virtual)"""
        exipicrename.set_dry_run(True)
        exipicrename.set_short_names(True)
        if VERBOSE:
            exipicrename.set_verbose(True)
        else:
            exipicrename.set_silent(True)
        exipicrename.set_clean_data_after_run(False)
        exipicrename.exipicrename(self.testfiles)
        index = self.TEST_FIRST_KEY
        e_dict = exipicrename.export_pic_dict()
        e_shortname = e_dict[index]['new_basename']
        self.assertEqual(
            e_shortname,
            self.TEST_SHORT_BASENAME,
            f"wrong shortname >{e_shortname}<"
        )
        exipicrename.clean_stored_data()

    def test_rename_with_dir(self):
        """test option --datadir (virtual)"""
        exipicrename.set_dry_run(True)
        exipicrename.set_use_date_dir(True)
        if VERBOSE:
            exipicrename.set_verbose(True)
        else:
            exipicrename.set_silent(True)
        exipicrename.set_clean_data_after_run(False)
        exipicrename.exipicrename(self.testfiles)
        e_dict = exipicrename.export_pic_dict()
        index = self.TEST_FIRST_KEY
        datestring = self.TEST_DICT_DEFAULT[index]['date']
        e_dir = e_dict[index]['new_dirname']

        self.assertTrue(
            e_dir.endswith(datestring),
            f"target path does not contain date sub-directory: >{e_dir}<"
        )
        exipicrename.clean_stored_data()

    def test_rename_additional_extension(self):
        """test option --oostring (virtual)"""
        exipicrename.set_dry_run(True)
        exipicrename.set_short_names(True)
        if VERBOSE:
            exipicrename.set_verbose(True)
        else:
            exipicrename.set_silent(True)
        exipicrename.set_clean_data_after_run(False)
        exipicrename.set_use_date_dir(False)
        exipicrename.set_ooc_extension(".foobar")
        exipicrename.set_use_ooc(True)
        exipicrename.exipicrename(self.testfiles)
        index = self.TEST_FIRST_KEY
        e_dict = exipicrename.export_pic_dict()
        e_extension = e_dict[index]['new_extension']
        self.assertEqual(
            e_extension,
            ".foobar" + exipicrename.get_jpg_out_extension(),
            f"additional extension wrong >{e_extension}<"
        )
        exipicrename.clean_stored_data()

def fill_tmpdir(temp_dir, source_dir, testfiles):
    """copy files to temporary testdir"""
    for _file in testfiles:
        if os.path.isfile(source_dir + _file):
            copy(source_dir + _file, temp_dir)

class TestExipicrenameReal(unittest.TestCase):
    """unittest class for exipicrename (in a temp environment with real files)"""

    test_dir, _ = os.path.split(os.path.abspath(__file__))

    testfiles = [
        'x_test.jpg',  # e520
        'x_test.jpg',  # same file e520
        'x_test.orf',  # "raw" (empty)
        'x_test.xml',  # "sidecar xml" (empty)
        'y_test.jpg',  # s4mini
        'yy_test.jpg', # duplicate
        'z_test.jpg',  # empty
        '0_test.jpg',  # file not existing
        ]

        #'20171123_164006__003__gt-i9195__3mm__f2-6__t17__iso125_1.jpg',
    source_dir = test_dir + "/fixtures/"

    def test_rename_default(self):
        """test default renaming (real files in tmp env)"""

        defaultfiles = [
            "20090604_184453__001__e-520__25mm__f2-8__t3200__iso100.jpg",
            "20090604_184453__001__e-520__25mm__f2-8__t3200__iso100.xml",
            "20090604_184453__001__e-520__25mm__f2-8__t3200__iso100.orf",
            "20171123_164006__002__s4mini__3mm__f2-6__t17__iso125.jpg",
            "20171123_164006__003__s4mini__3mm__f2-6__t17__iso125_1.jpg",
            'z_test.jpg'
            ]

        if VERBOSE:
            exipicrename.set_verbose(True)
        else:
            exipicrename.set_silent(True)

        exipicrename.set_short_names(False)
        exipicrename.set_use_ooc(False)
        exipicrename.set_dry_run(False)
        exipicrename.set_use_date_dir(False)

        with TemporaryDirectory() as temp_dir:

            fill_tmpdir(temp_dir, self.source_dir, self.testfiles)

            realfiles = [temp_dir + "/" + e for e in os.listdir(temp_dir)]

            exipicrename.exipicrename(realfiles)

            defaultfiles.sort()
            tmpdirfiles = os.listdir(temp_dir)
            tmpdirfiles.sort()
            self.assertEqual(defaultfiles, tmpdirfiles)

    def test_rename_short(self):
        """test renaming with --short (real files in tmp env)"""

        defaultfiles = [
            "20090604_184453__001.jpg",
            "20090604_184453__001.xml",
            "20090604_184453__001.orf",
            "20171123_164006__002.jpg",
            "20171123_164006__003_1.jpg",
            'z_test.jpg'
            ]

        if VERBOSE:
            exipicrename.set_verbose(True)
        else:
            exipicrename.set_silent(True)

        exipicrename.set_short_names(True)
        exipicrename.set_use_ooc(False)
        exipicrename.set_dry_run(False)
        exipicrename.set_use_date_dir(False)

        with TemporaryDirectory() as temp_dir:

            fill_tmpdir(temp_dir, self.source_dir, self.testfiles)

            realfiles = [temp_dir + "/" + e for e in os.listdir(temp_dir)]

            exipicrename.exipicrename(realfiles)

            defaultfiles.sort()
            tmpdirfiles = os.listdir(temp_dir)
            tmpdirfiles.sort()
            self.assertEqual(defaultfiles, tmpdirfiles)

    def test_rename_datadir(self):
        """test renaming with --datadir (real files in tmp env)"""

        dirs = [
            "2009-06-04",
            "2017-11-23",
            ]

        if VERBOSE:
            exipicrename.set_verbose(True)
        else:
            exipicrename.set_silent(True)

        exipicrename.set_short_names(True)
        exipicrename.set_use_ooc(False)
        exipicrename.set_dry_run(False)
        exipicrename.set_use_date_dir(True)

        with TemporaryDirectory() as temp_dir:

            fill_tmpdir(temp_dir, self.source_dir, self.testfiles)

            realfiles = [temp_dir + "/" + e for e in os.listdir(temp_dir)]

            exipicrename.exipicrename(realfiles)

            #print(os.listdir(temp_dir))

            for _dir in dirs:
                self.assertTrue(os.path.isdir(os.path.join(temp_dir, _dir)))

if __name__ == '__main__':
    unittest.main()
