import json
import sdc_client

from ..conftest import get_input_file_path
from agent import source, cli


class TestInputBase(object):
    __test__ = False
    params = {}

    def test_create_source_with_file(self, cli_runner, file_name):
        input_file_path = get_input_file_path(file_name + '.json')
        result = cli_runner.invoke(cli.source.create, ['-f', input_file_path], catch_exceptions=False)
        assert result.exit_code == 0
        with open(input_file_path) as f:
            sources = json.load(f)
            for source_ in sources:
                assert source.repository.exists(f"{source_['name']}")

    def test_create_with_file(self, cli_runner, file_name):
        input_file_path = get_input_file_path(file_name + '.json')
        result = cli_runner.invoke(cli.pipeline.create, ['-f', input_file_path], catch_exceptions=False)
        assert result.exit_code == 0
        with open(input_file_path) as f:
            for pipeline_config in json.load(f):
                assert sdc_client.exists(pipeline_config['pipeline_id'])