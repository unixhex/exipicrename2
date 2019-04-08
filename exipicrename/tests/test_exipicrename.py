"""unittest for exipicrename"""
import unittest
import exipicrename
import os

#VERBOSE = True
VERBOSE = False

class TestExipicrename(unittest.TestCase):
    """unittest class for exipicrename"""

    test_dirname, _ = os.path.split(os.path.abspath(__file__)) 

    testfiles = [test_dirname + '/fixtures/x_test.jpg',]

    TEST_DICT_DEFAULT = {
        '20090604_184453_0': {
            'timestamp': '20090604_184453',
            'duplicate': 0,
            'orig_basename': 'x_test',
            'new_basename': '20090604_184453__001__e-520__25mm__f2-8__iso100',
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
            'new_basename': '20090604_184453__001__e-520__25mm__f2-8__iso100',
            'orig_extension': '.xml',
            'new_extension': '.xml'},
        '20090604_184453_0_raw': {
            #'orig_dirname': 'absolut path, not usefull for tests',
            #'new_dirname': 'absolut path, not usefull for tests',
            'orig_basename': 'x_test',
            'new_basename': '20090604_184453__001__e-520__25mm__f2-8__iso100',
            'orig_extension': '.orf',
            'new_extension': '.orf'
            }
        }
    TEST_FIRST_KEY = '20090604_184453_0'
    TEST_SHORT_BASENAME = '20090604_184453__001'

    def test_dry_run_false(self):
        """test without option --dry-run"""
        exipicrename.set_dry_run(False)
        self.assertFalse(exipicrename.is_dry_run(), f"dry run should be set to False")
    def test_dry_run_true(self):
        """test option --dry-run"""
        exipicrename.set_dry_run(True)
        self.assertTrue(exipicrename.is_dry_run(), f"dry run should be set to True")

    def test_rename_default(self):
        """test default renaming"""
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
        """test option --short"""
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
        """test option --datadir"""
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
        """test option --oostring"""
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


if __name__ == '__main__':
    unittest.main()
