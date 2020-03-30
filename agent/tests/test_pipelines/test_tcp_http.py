import os
import pytest
import socket

from ..fixtures import cli_runner, get_input_file_path
from agent.pipeline import cli as pipeline_cli, load_object as load_pipeline
from agent.source import cli as source_cli, Source, TYPE_SPLUNK
from agent.streamsets_api_client import api_client
from .test_zpipeline_base import TestPipelineBase, pytest_generate_tests


class TestTCPServer(TestPipelineBase):

    __test__ = True
    params = {
        'test_create_source_with_file': [{'file_name': 'tcp_sources'}],
        'test_create_with_file': [{'file_name': 'tcp_pipelines'}],
        'test_start': [{'name': 'test_tcp_log'}, {'name': 'test_tcp_json'}, {'name': 'test_tcp_csv'}],
        'test_stop': [{'name': 'test_tcp_log'}, {'name': 'test_tcp_json'}, {'name': 'test_tcp_csv'}],
        'test_output': [
            {'name': 'test_tcp_csv', 'output': 'json_value_property_tags.json', 'pipeline_type': TYPE_SPLUNK},
            {'name': 'test_tcp_log', 'output': 'log.json', 'pipeline_type': TYPE_SPLUNK},
            {'name': 'test_tcp_json', 'output': 'json_value_property.json', 'pipeline_type': TYPE_SPLUNK}
        ],
        'test_delete_pipeline': [{'name': 'test_tcp_log'}, {'name': 'test_tcp_json'}, {'name': 'test_tcp_csv'}],
        'test_source_delete': [{'name': 'test_tcp_log'}, {'name': 'test_tcp_json'}, {'name': 'test_tcp_csv'}],
    }

    def test_source_create(self, cli_runner):
        grok_file_path = get_input_file_path('grok_patterns.txt')
        result = cli_runner.invoke(source_cli.create,
                                   input="splunk\ntest_tcp_log\n9999\nLOG\n" + grok_file_path + "\n%{NONNEGINT:timestamp_unix_ms} %{TIMESTAMP:timestamp_string} %{NONNEGINT:ver} %{WORD} %{WORD:Country} %{WORD:AdType} %{WORD:Exchange} %{NUMBER:Clicks}\n")
        assert result.exit_code == 0
        assert os.path.isfile(os.path.join(Source.DIR, 'test_tcp_log.json'))

    def test_create(self, cli_runner):
        result = cli_runner.invoke(pipeline_cli.create,
                                   input=f"test_tcp_log\ntest_tcp_log\n\nn\nClicks:gauge\nClicks:clicks\ntimestamp_unix_ms\nunix_ms\nver Country\nExchange optional_dim\n\n")
        assert result.exit_code == 0
        assert api_client.get_pipeline('test_tcp_log')

    def test_create_source_with_file(self, cli_runner, file_name):
        super().test_create_source_with_file(cli_runner, file_name)

    def test_create_with_file(self, cli_runner, file_name):
        super().test_create_with_file(cli_runner, file_name)

    def test_edit(self, cli_runner):
        pytest.skip()

    def test_edit_with_file(self, cli_runner, file_name=None):
        pytest.skip()

    def test_start(self, cli_runner, name):
        result = cli_runner.invoke(pipeline_cli.start, [name])
        assert result.exit_code == 0
        assert api_client.get_pipeline_status(name)['status'] == 'RUNNING'

        # streams data
        pipeline = load_pipeline(name)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('dc', int(pipeline.source.config['conf.ports'][0])))

        data = {'LOG': 'log.txt', 'DELIMITED': 'test.csv', 'JSON': 'test_json_items'}
        with open(f'/home/{data[pipeline.source.config["conf.dataFormat"]]}', 'r') as f:
            for line in f.readlines():
                s.sendall(f'{line}\n'.encode())
        s.close()

    def test_output_exists(self, cli_runner, name=None):
        pytest.skip()