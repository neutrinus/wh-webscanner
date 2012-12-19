
import os
import shutil
import tempfile

import sh
import pytest

from ..utils import ImageOptimizer
'''
This modue does not contain whole beautiful tests, it only check that file
after all optimize opreration is created (and it hopes that everything during
generating output was ok).
'''


def test_file_does_not_exist():
    should_fail = False
    i = ImageOptimizer()
    optimized_jpeg = os.path.join(i.tmp_path, 'qwewqeqweqwe.jpg')
    with pytest.raises(sh.ErrorReturnCode_1):
        i.optimize_jpg('adsfsdfsafsaf/21k31n23ue.jpg', optimized_jpeg)
    if os.path.exists(optimized_jpeg):
        if os.path.getsize(optimized_jpeg) > 0:
            should_fail = True
        os.unlink(optimized_jpeg)
    if should_fail:
        raise AssertionError('%s - this file should not exists')


@pytest.mark.parametrize(['file', 'type'], [
    ['example.jpg', 'JPEG'],
    ['example.png', 'PNG'],
    ['example.gif', 'PNG'],
    ['example_agif.gif', 'AGIF']])
def test_image_optimizer_on_example(file, type):
    new_tmp_path = tempfile.mkdtemp()

    # shere new_tmp_path for tmp files and results files
    i = ImageOptimizer(new_tmp_path)
    optimized_files_path = new_tmp_path

    optimized_file_path = i.optimize_image(os.path.join(os.path.dirname(__file__), 'test_files/%s' % file), optimized_files_path)
    assert optimized_file_path
    assert os.path.exists(optimized_file_path)
    assert i.identify_image_type(optimized_file_path) == type
    os.unlink(optimized_file_path)

    # after removing optimized_file_path directory should be empty (tmp files
    # should be removed before by the optimizer)
    assert not os.listdir(new_tmp_path)
    shutil.rmtree(new_tmp_path)
