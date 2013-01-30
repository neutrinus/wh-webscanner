import os

import pytest

from scanner.plugins.tests.helpers import PluginTestBase, TempDirMixin
from ..screenshots import PluginMakeScreenshots as Plugin


class TestScreenshots(TempDirMixin, PluginTestBase):

    plugin_class = Plugin

    def test_make_screenshot_for_test(self, client):
        from scanner.models import Tests, CommandQueue, STATUS

        scr = self.plugin_class()
        test = Tests(check_seo=True,
                     download_path=os.path.join(os.path.dirname(__file__), 'test_files'))
        test.save()
        cmd = CommandQueue(test=test)
        cmd.save()
        assert STATUS.success == scr.run(cmd)
