import os
import shutil
import tempfile

import pytest

from ..check_optiimg import PluginOptiimg
from scanner.models import Tests, CommandQueue, STATUS


def test_directory_does_not_exist_fail():
    PluginOptiimg.OPTIMIZED_IMAGES_PATH = os.path.join(tempfile.mkdtemp(), PluginOptiimg.OPTIMIZED_IMAGES_DIR_NAME)
    try:
        with pytest.raises(OSError):
            PluginOptiimg()
    finally:
        if os.path.isdir(PluginOptiimg.OPTIMIZED_IMAGES_PATH):
            shutil.rmtree(PluginOptiimg.OPTIMIZED_IMAGES_PATH)


def test_check_optiimg(client):
    PluginOptiimg.OPTIMIZED_IMAGES_PATH = os.path.join(tempfile.mkdtemp(), PluginOptiimg.OPTIMIZED_IMAGES_DIR_NAME)
    os.makedirs(PluginOptiimg.OPTIMIZED_IMAGES_PATH)

    opti = PluginOptiimg()
    test = Tests(check_performance=True,
                 download_path=os.path.join(os.path.dirname(__file__), 'test_files'))
    test.save()
    cmd = CommandQueue(test=test)
    cmd.save()
    assert STATUS.success == opti.run(cmd)

    # remove unused tmp dir
    shutil.rmtree(PluginOptiimg.OPTIMIZED_IMAGES_PATH)
