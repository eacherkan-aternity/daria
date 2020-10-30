import json
import requests
import time
import urllib.parse
import click

from sqlalchemy import Column, Integer, String
from agent.modules.db import Entity
from agent.modules.logger import get_logger
from agent.modules.constants import STREAMSETS_PREVIEW_TIMEOUT

logger = get_logger(__name__)


def endpoint(func):
    """
    Decorator for api endpoints. Logs errors and returns json response

    :param func:
    :return:
    """

    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        try:
            res.raise_for_status()
            if res.text:
                return res.json()
            return
        except requests.exceptions.HTTPError:
            if res.text:
                try:
                    response = res.json()
                    logger.exception(response['RemoteException'])
                    raise StreamSetsApiClientException(response['RemoteException']['message'])
                except json.decoder.JSONDecodeError:
                    raise StreamSetsApiClientException(res.text)
            raise

    return wrapper


class StreamSets(Entity):
    __tablename__ = 'streamsets'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    username = Column(String)
    password = Column(String)

    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password


class StreamSetsApiClient:
    def __init__(self, streamsets: StreamSets):
        self.base_url = streamsets.url
        self.session = requests.Session()
        self.session.keep_alive = False
        self.session.auth = (streamsets.username, streamsets.password)
        self.session.headers.update({'X-Requested-By': 'sdc'})

    def _build_url(self, *args):
        return urllib.parse.urljoin(self.base_url, '/'.join(['/rest/v1', *args]))

    @endpoint
    def create_pipeline(self, name: str):
        logger.info(f'Creating pipeline: {name}')
        return self.session.put(self._build_url('pipeline', name))

    @endpoint
    def update_pipeline(self, pipeline_id: str, pipeline_config: dict):
        logger.info(f'Updating pipeline: {pipeline_id}')
        return self.session.post(self._build_url('pipeline', pipeline_id), json=pipeline_config)

    @endpoint
    def start_pipeline(self, pipeline_id: str):
        logger.info(f'Start pipeline: {pipeline_id}')
        return self.session.post(self._build_url('pipeline', pipeline_id, 'start'))

    @endpoint
    def stop_pipeline(self, pipeline_id: str):
        logger.info(f'Stop pipeline: {pipeline_id}')
        return self.session.post(self._build_url('pipeline', pipeline_id, 'stop'))

    @endpoint
    def force_stop(self, pipeline_id: str):
        logger.info(f'Force stop pipeline: {pipeline_id}')
        return self.session.post(self._build_url('pipeline', pipeline_id, 'forceStop'))

    @endpoint
    def get_pipelines(self, order_by='NAME', order='ASC', label=None):
        logger.info('Get pipelines')
        params = {'orderBy': order_by, 'order': order}
        if label:
            params['label'] = label
        return self.session.get(self._build_url('pipelines'), params=params)

    @endpoint
    def get_pipeline(self, pipeline_id: str):
        logger.info(f'Get pipeline {pipeline_id}')
        params = {'pipelineId': pipeline_id}
        return self.session.get(self._build_url('pipelines'), params=params)

    @endpoint
    def get_pipeline_statuses(self) -> requests.Response:
        logger.info('Get pipelines status')
        return self.session.get(self._build_url('pipelines', 'status'))

    @endpoint
    def delete_pipeline(self, pipeline_id: str):
        logger.info(f'Delete pipeline: {pipeline_id}')
        return self.session.delete(self._build_url('pipeline', pipeline_id))

    @endpoint
    def get_pipeline_logs(self, pipeline_id: str, severity=None):
        """
        :param pipeline_id: string
        :param severity: string [INFO, ERROR], default - None
        :return:
        """
        logger.info(f'Get pipeline logs: {pipeline_id}, logging severity:{severity}')
        params = {'pipeline': pipeline_id, 'endingOffset': -1}
        if severity:
            params['severity'] = severity
        return self.session.get(self._build_url('system', 'logs'), params=params)

    @endpoint
    def get_pipeline(self, pipeline_id: str):
        logger.info(f'Get pipeline {pipeline_id}')
        return self.session.get(self._build_url('pipeline', pipeline_id))

    @endpoint
    def get_pipeline_status(self, pipeline_id: str):
        logger.info(f'Get pipeline status {pipeline_id}')
        return self.session.get(self._build_url('pipeline', pipeline_id, 'status'))

    @endpoint
    def get_pipeline_history(self, pipeline_id: str):
        logger.info(f'Get pipeline history {pipeline_id}')
        return self.session.get(self._build_url('pipeline', pipeline_id, 'history'))

    @endpoint
    def get_pipeline_metrics(self, pipeline_id: str):
        logger.info(f'Get pipeline metrics {pipeline_id}')
        return self.session.get(self._build_url('pipeline', pipeline_id, 'metrics'))

    @endpoint
    def reset_pipeline(self, pipeline_id: str):
        logger.info(f'Reset pipeline offset {pipeline_id}')
        return self.session.post(self._build_url('pipeline', pipeline_id, 'resetOffset'))

    @endpoint
    def validate(self, pipeline_id: str):
        logger.info(f'Validate pipeline {pipeline_id}')
        return self.session.get(self._build_url('pipeline', pipeline_id, 'validate'),
                                params={'timeout': STREAMSETS_PREVIEW_TIMEOUT})

    @endpoint
    def create_preview(self, pipeline_id: str):
        logger.info(f'Create pipeline {pipeline_id} preview')
        return self.session.post(self._build_url('pipeline', pipeline_id, 'preview'),
                                 params={'timeout': STREAMSETS_PREVIEW_TIMEOUT})

    @endpoint
    def get_preview(self, pipeline_id: str, previewer_id: str):
        logger.info(f'Validate pipeline {pipeline_id}')
        return self.session.get(self._build_url('pipeline', pipeline_id, 'preview', previewer_id))

    @endpoint
    def get_preview_status(self, pipeline_id: str, previewer_id: str):
        logger.info(f'Validate pipeline {pipeline_id}')
        return self.session.get(self._build_url('pipeline', pipeline_id, 'preview', previewer_id, 'status'))

    def wait_for_preview(self, pipeline_id: str, preview_id: str, tries=6, initial_delay=2):
        for i in range(1, tries + 1):
            response = self.get_preview_status(pipeline_id, preview_id)
            if response['status'] == 'TIMED_OUT':
                raise StreamSetsApiClientException(f"No data. Connection timed out")

            if response['status'] not in ['VALIDATING', 'CREATED', 'RUNNING', 'STARTING', 'FINISHING', 'CANCELLING',
                                          'TIMING_OUT']:
                break

            delay = initial_delay ** i
            if i == tries:
                raise StreamSetsApiClientException(f"No data")
            print(f"Waiting for data. Check again after {delay} seconds...")
            time.sleep(delay)

        preview_data = self.get_preview(pipeline_id, preview_id)

        errors = []
        if preview_data['status'] == 'RUN_ERROR':
            errors.append(preview_data['message'])
        if preview_data['issues']:
            for stage, data in preview_data['issues']['stageIssues'].items():
                for issue in data:
                    errors.append(issue['message'])
            for issue in preview_data['issues']['pipelineIssues']:
                errors.append(issue['message'])

        if preview_data['batchesOutput']:
            for batch in preview_data['batchesOutput']:
                for stage in batch:
                    if stage['errorRecords']:
                        for record in stage['errorRecords']:
                            errors.append(record['header']['errorMessage'])

        return preview_data, errors

    @endpoint
    def get_pipeline_errors(self, pipeline_id: str, stage_name):
        logger.info(f'Get pipeline {pipeline_id} errors')
        return self.session.get(self._build_url('pipeline', pipeline_id, 'errorRecords'),
                                params={'stageInstanceName': stage_name})

    def wait_for_status(self, pipeline_id: str, status: str, tries: int = 5, initial_delay: int = 3):
        for i in range(1, tries + 1):
            response = self.get_pipeline_status(pipeline_id)
            if response['status'] == status:
                return True
            delay = initial_delay ** i
            if i == tries:
                raise PipelineFreezeException(
                    f"Pipeline {pipeline_id} is still {response['status']} after {tries} tries")
            print(f"Pipeline {pipeline_id} is {response['status']}. Check again after {delay} seconds...")
            time.sleep(delay)


class StreamSetsApiClientException(click.ClickException):
    pass


class PipelineFreezeException(Exception):
    pass