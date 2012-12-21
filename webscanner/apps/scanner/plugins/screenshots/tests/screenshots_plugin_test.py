import os

import pytest

from scanner.plugins.tests.helpers import PluginTestBase, TempDirMixin
from ..screenshots import PluginMakeScreenshots as Plugin


class TestScreenshots(TempDirMixin, PluginTestBase):

    plugin_class = Plugin

    def test_directory_does_not_exist_fail(self):
        self.plugin_class.SCREENSHOTS_PATH = '/something_that_probably_may_not_exists/wqekn12313i321/'
        with pytest.raises(OSError):
            self.plugin_class()

    def test_make_screenshot_for_test(self, client):
        from scanner.models import Tests, CommandQueue, STATUS
        self.plugin_class.SCREENSHOTS_PATH = self.mkdtemp()

        scr = self.plugin_class()
        test = Tests(check_seo=True,
                     download_path=os.path.join(os.path.dirname(__file__), 'test_files'))
        test.save()
        cmd = CommandQueue(test=test)
        cmd.save()
        assert STATUS.success == scr.run(cmd)
