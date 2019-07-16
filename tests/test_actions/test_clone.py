from tests.test_actions import *
import sys
from ltk.actions.clone_action import *
from ltk.actions.add_action import AddAction
from ltk.actions.rm_action import RmAction
from ltk.actions.config_action import ConfigAction
import os
import unittest

@unittest.skip("skipping until clone is fully functional")
class TestClone(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_config()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def setUp(self):
        self.action = CloneAction(os.getcwd())
        self.add_action = AddAction(os.getcwd())
        self.added_directories = []
        self.config_action = ConfigAction(os.getcwd())
        self.rm_action = RmAction(os.getcwd())
        self.dir_path1 = os.path.join(os.getcwd(), 'dir1')
        self.added_directories.append(self.dir_path1)
        create_directory(self.dir_path1)
        self.dir_path2 = os.path.join(os.getcwd(), 'dir2')
        self.added_directories.append(self.dir_path2)
        create_directory(self.dir_path2)
        self.dir_path3 = os.path.join(os.getcwd(), 'dir1','dir3')
        self.added_directories.append(self.dir_path3)
        create_directory(self.dir_path3)
        self.delete_directory(os.path.join(os.getcwd(), 'ja-JP'))
        self.delete_directory(os.path.join(os.getcwd(), 'es-MX'))
        self.delete_directory(os.path.join(os.getcwd(), 'downloads'))

    def tearDown(self):
        for d in self.added_directories:
            self.delete_directory(d)

        self.rm_action.close()
        self.action.close()

    def test_clone_single_locale(self):
        #currently doesn't work, clone needs to be fixed
        os.system('ltk config -t ja-JP')
        self.add_action.add_action([self.dir_path1])
        self.add_action.add_action([self.dir_path2])
        os.system('ltk clone')
        assert os.path.isdir(os.path.join(os.getcwd(), 'ja-JP'))
        self.added_directories.append(os.path.join(os.getcwd(), 'ja-JP'))
        assert os.path.isdir(os.path.join(os.getcwd(), 'ja-JP','dir1'))
        assert os.path.isdir(os.path.join(os.getcwd(), 'ja-JP','dir1','dir3'))
        assert os.path.isdir(os.path.join(os.getcwd(), 'ja-JP','dir2'))

    def test_clone_multi_locale(self):
        #currently doesn't work, clone needs to be fixed
        os.system('ltk config -t ja-JP,es-MX')
        self.add_action.add_action([self.dir_path1])
        self.add_action.add_action([self.dir_path2])
        os.system('ltk clone')
        assert os.path.isdir(os.path.join(os.getcwd(), 'ja-JP'))
        self.added_directories.append(os.path.join(os.getcwd(), 'ja-JP'))
        assert os.path.isdir(os.path.join(os.getcwd(), 'ja-JP','dir1'))
        assert os.path.isdir(os.path.join(os.getcwd(), 'ja-JP','dir1','dir3'))
        assert os.path.isdir(os.path.join(os.getcwd(), 'ja-JP','dir2'))
        assert os.path.isdir(os.path.join(os.getcwd(), 'es-MX'))
        self.added_directories.append(os.path.join(os.getcwd(), 'es-MX'))
        assert os.path.isdir(os.path.join(os.getcwd(), 'es-MX','dir1'))
        assert os.path.isdir(os.path.join(os.getcwd(), 'es-MX','dir1','dir3'))
        assert os.path.isdir(os.path.join(os.getcwd(), 'es-MX','dir2'))

    def test_clone_root(self):
        #clone needs to be fixed before a test can be written
        assert True

    def test_clone_root_only(self):
        #clone needs to be fixed before a test can be written
        assert True

    def test_clone_single_folder(self):
        #currently doesn't work, clone needs to be fixed
        os.system('ltk config -t ja-JP')
        self.add_action.add_action([self.dir_path2])
        os.system('ltk clone')
        assert os.path.isdir(os.path.join(os.getcwd(), 'ja-JP'))
        self.added_directories.append(os.path.join(os.getcwd(), 'ja-JP'))
        assert not os.path.isdir(os.path.join(os.getcwd(), 'ja-JP','dir1'))
        assert not os.path.isdir(os.path.join(os.getcwd(), 'ja-JP','dir1','dir3'))
        assert not os.path.isdir(os.path.join(os.getcwd(), 'ja-JP','dir2')) #because it was only one folder, the locale folder is used instead of dir2

    def test_clone_with_download_folder(self):
        #currently doesn't work, clone needs to be fixed
        self.download_path = os.path.join(os.getcwd(), 'downloads')
        self.added_directories.append(self.download_path)
        create_directory(self.download_path)
        os.system('ltk config -d downloads')
        os.system('ltk config -t ja-JP')
        self.add_action.add_action([self.dir_path1])
        self.add_action.add_action([self.dir_path2])
        os.system('ltk clone')
        assert os.path.isdir(os.path.join(os.getcwd(), 'downloads','ja-JP'))
        self.added_directories.append(os.path.join(os.getcwd(), 'downloads','ja-JP'))
        assert os.path.isdir(os.path.join(os.getcwd(), 'downloads','ja-JP','dir1'))
        assert os.path.isdir(os.path.join(os.getcwd(), 'downloads','ja-JP','dir1','dir3'))
        assert os.path.isdir(os.path.join(os.getcwd(), 'downloads','ja-JP','dir2'))

    def delete_directory(self, dir_path):
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            for subdir in os.listdir(dir_path):
                if(dir_path.endswith(os.sep)):
                    self.delete_directory(dir_path+subdir)
                else:
                    self.delete_directory(dir_path+os.sep+subdir)
            print("disassociating directory: "+dir_path.replace(os.getcwd()+os.sep, ''))
            self.rm_action.rm_action([dir_path.replace(os.getcwd()+os.sep, '')], remote=True, force=True)
            print("deleting directory: "+dir_path)
            os.rmdir(dir_path)

#See ticket LP-28910
#part of clone fix:
#126                if os.path.isdir(path):
#127!                    matched_dirs.append('')
#128                    for root, subdirs, files in os.walk(path):