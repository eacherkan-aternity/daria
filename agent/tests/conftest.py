import json
import os
import pytest

from click.testing import CliRunner
from agent import di
from agent.api import main

DUMMY_DESTINATION_OUTPUT_PATH = '/output'
TEST_DATASETS_PATH = '/home'

INPUT_FILES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'input_files')


@pytest.fixture(scope="session")
def cli_runner():
    di.init()
    yield CliRunner()


@pytest.fixture
def api_client():
    main.app.testing = True
    with main.app.test_client() as client:
        di.init()
        yield client


def get_output(file_name):
    for filename in os.listdir(DUMMY_DESTINATION_OUTPUT_PATH):
        if filename == file_name:
            with open(os.path.join(DUMMY_DESTINATION_OUTPUT_PATH, filename)) as f:
                return json.load(f)


def get_input_file_path(name):
    return os.path.join(INPUT_FILES_DIR, f'{name}')


def pytest_generate_tests(metafunc):
    # called once per each test function
    if metafunc.cls is None or not hasattr(metafunc.cls, 'params') or metafunc.function.__name__ not in metafunc.cls.params:
        return
    funcarglist = metafunc.cls.params[metafunc.function.__name__]
    function_argnames = set(metafunc.function.__code__.co_varnames[:metafunc.function.__code__.co_argcount])
    params = sorted(list(function_argnames - {'self', 'cli_runner', 'api_client'}))
    metafunc.parametrize(params, [[funcargs.get(name, None) for name in params] for funcargs in funcarglist])


def generate_input(input_: dict) -> str:
    return '\n'.join(map(
        lambda x: str(x),
        input_.values()
    ))
