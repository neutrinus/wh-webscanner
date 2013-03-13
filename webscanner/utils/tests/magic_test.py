
import os
import pytest

from .. import magic

@pytest.mark.parametrize(('file_name', 'mime', 'exception'),
                         (
                             ('yahoo.html', 'text/html', 0),
                             ('file1.js', 'application/javascript', 0),
                             ('file2.js', 'application/javascript', 0),
                             ('file3.js', 'application/javascript', 0),
                             ('file1.css', 'text/css', 0),
                             ('file2.css', 'text/css', 0),
                             ('file3.css', 'text/css', 0),
                             ('file4.css', 'text/css', 0),
                         ))
def test_mime_files(file_name, mime, exception):
    file_path = os.path.join(os.path.dirname(__file__), 'magic_samples', file_name)
    m = magic.Magic()
    assert m.advanced_for_file(file_path) == mime
    #print m._classifier._cls.show_most_informative_features()
