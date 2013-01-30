import os
import shutil
import tempfile

import pytest

from ..check_optiimg import PluginOptiimg
from scanner.models import Tests, CommandQueue, STATUS


def test_check_optiimg(client):
    opti = PluginOptiimg()
    test = Tests(check_performance=True,
                 download_path=os.path.join(os.path.dirname(__file__), 'test_files'))
    test.save()
    cmd = CommandQueue(test=test)
    cmd.save()
    assert STATUS.success == opti.run(cmd)
