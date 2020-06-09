# standard imports
import os
import uuid

# third party imports
import pytest

# platform imports
import config
from files.sync import FileSyncer
from files.gitlab import Gitlab

def test_files():
    uu = str(uuid.uuid4())
    randomfilename = '/tmp/' + uu + '/foo'
    fs = FileSyncer('.', '/tmp/' + randomfilename + '/foo', None)
    fs.sync([])

@pytest.mark.skipif(not config.AWS_HAVE_CREDENTIALS, reason='aws not set up, skipping s3 test')
def test_s3():
    uu = str(uuid.uuid4())
    randomfilename = '/tmp/' + uu + '/foo'
    fs = Gitlab(config.TEST_BUCKET)
    remote_files = ['foo.txt', 'bar.txt']
    r = fs.sync(remote_files)
    for f in remote_files:
        assert(f in r)
