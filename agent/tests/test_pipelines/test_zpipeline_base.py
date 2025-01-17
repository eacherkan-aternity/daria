import json
import os
import time
import sdc_client

from ..conftest import get_output
from agent import pipeline, source, cli


class TestPipelineBase(object):
    __test__ = False

    params = {}

    def test_start(self, cli_runner, name: str, sleep: int):
        result = cli_runner.invoke(cli.pipeline.start, [name], catch_exceptions=False)
        assert result.exit_code == 0
        if not sleep:
            sleep = 10
        time.sleep(sleep)

        pipeline_ = pipeline.repository.get_by_id(name)
        assert sdc_client.get_pipeline_status(pipeline_) == pipeline.Pipeline.STATUS_RUNNING
        # give pipelines some time to send data
        # at high load there might be lag before status is updated in the db, so checking after some time
        assert pipeline_.status == pipeline.Pipeline.STATUS_RUNNING

    def test_info(self, cli_runner, name):
        result = cli_runner.invoke(cli.pipeline.info, [name], catch_exceptions=False)
        assert result.exit_code == 0

    def test_stop(self, cli_runner, name):
        result = cli_runner.invoke(cli.pipeline.stop, [name], catch_exceptions=False)
        assert result.exit_code == 0
        assert sdc_client.get_pipeline_status(pipeline.repository.get_by_id(name)) == pipeline.Pipeline.STATUS_STOPPED

    def test_force_stop(self, cli_runner, name):
        result = cli_runner.invoke(cli.pipeline.force_stop, [name], catch_exceptions=False)
        assert result.exit_code == 0

    def test_reset(self, cli_runner, name):
        result = cli_runner.invoke(cli.pipeline.reset, [name], catch_exceptions=False)
        assert result.exit_code == 0

    def test_output(self, name, pipeline_type, output):
        expected_output = get_expected_output(name, output, pipeline_type)
        assert get_output(f'{name}_{pipeline_type}.json') == expected_output

    def test_output_schema(self, name, pipeline_type, output):
        expected_output = get_expected_schema_output(name, output, pipeline_type)
        assert get_output(f'{name}_{pipeline_type}.json') == expected_output

    def test_delete_pipeline(self, cli_runner, name):
        result = cli_runner.invoke(cli.pipeline.delete, [name], catch_exceptions=False)
        assert result.exit_code == 0
        assert not sdc_client.exists(name)
        assert not pipeline.repository.exists(name)

    def test_source_delete(self, cli_runner, name):
        result = cli_runner.invoke(cli.source.delete, [name], catch_exceptions=False)
        assert result.exit_code == 0
        assert not source.repository.exists(name)


def get_expected_output(pipeline_id: str, expected_output_file: str, pipeline_type: str) -> list:
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), f'expected_output/{expected_output_file}')) as f:
        expected_output = json.load(f)
        for item in expected_output:
            item['tags']['pipeline_id'] = [pipeline_id]
            item['tags']['pipeline_type'] = [pipeline_type]
    return expected_output


def get_expected_schema_output(pipeline_id: str, expected_output_file: str, pipeline_type: str) -> list:
    expected_output = get_expected_output(pipeline_id, expected_output_file, pipeline_type)
    for record in expected_output:
        record['schemaId'] = get_schema_id(pipeline_id)
    return expected_output


def get_schema_id(pipeline_id: str) -> str:
    return f'{pipeline_id}-1234'
