import os
import sys
import shutil
import tempfile

from ..plugin import PluginMixin


class TempDirMixin(object):
    '''
    This is for pytest, so instead of __init__ it has `setup` :(
    '''
    def setup_method(self, method):
        # all this temp dirs will be removed after test
        self._temp_dir_paths = []

    def mkdtemp(self, subdir_name=None):
        '''
        It makes temp directory with `tempfile.mkdtemp`. If you specify `subdir_name`
        this will be joined to path generated by `mkdtemp` and this directory will
        be created with `os.makedirs`.

        Each directory created with this method is placed on the stack of temporary
        directories and all of them will be removed on `tear_down`.
        '''
        tmp_dir_path = tempfile.mkdtemp()
        self._temp_dir_paths.append(tmp_dir_path)
        if subdir_name:
            new_tmp = os.path.join(tmp_dir_path, subdir_name)
            os.makedirs(new_tmp)
            return new_tmp
        return tmp_dir_path

    def _remove_temp_dirs(self):
        for tmp_dir_path in self._temp_dir_paths:
            if os.path.isdir(tmp_dir_path):
                shutil.rmtree(tmp_dir_path)

    def teardown_method(self, method):
        self._remove_temp_dirs()


class PluginTestBase(object):

    plugin_class = NotImplemented

    def setup(self):
        if not type(self.plugin_class) == type or not issubclass(self.plugin_class, PluginMixin):
            raise AssertionError('''You have to use a subclass \
of PluginMixin as `plugin_class` attribute in your test class {cls} \
in file {file} which inherits from PluginTestBase'''.format(cls=self.__class__,
                                                            file=sys.modules[self.__class__.__module__].__file__))
        #super(PluginTestBase, self).setup()
