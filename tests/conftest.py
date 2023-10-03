import shutil

import pytest
from config_keeper import settings

from tests.helpers import TMP_DIR, id_generator

get_config_file_id = id_generator()


@pytest.fixture(scope='session', autouse=True)
def _setup_session():
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True)


@pytest.fixture(autouse=True)
def _mock_config_file():
    settings.CONFIG_FILE = TMP_DIR / f'test_config_{get_config_file_id()}.yaml'
