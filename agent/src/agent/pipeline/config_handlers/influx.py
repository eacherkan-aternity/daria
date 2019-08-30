import os

from .base import BaseConfigHandler, ConfigHandlerException
from agent.logger import get_logger
from datetime import datetime, timedelta
from influxdb import InfluxDBClient
from urllib.parse import urljoin, urlparse

logger = get_logger(__name__)


class InfluxConfigHandler(BaseConfigHandler):
    DECLARE_VARS_JS = """/*
state['MEASUREMENT_NAME'] = 'clicks';
state['REQUIRED_DIMENSIONS'] = ['AdType', 'Exchange'];
state['OPTIONAL_DIMENSIONS'] = ['ver', 'AdSize', 'Country'];
state['VALUES_COLUMNS'] = ['value'];
state['TARGET_TYPE'] = 'gauge';
state['VALUE_CONSTANT'] = 1
state['HOST_ID'] = 'acgdhjehfje'
*/

state['MEASUREMENT_NAME'] = '{measurement_name}';
state['REQUIRED_DIMENSIONS'] = {required_dimensions};
state['OPTIONAL_DIMENSIONS'] = {optional_dimensions};
state['VALUES_COLUMNS'] = {values};
state['TARGET_TYPE'] = '{target_type}';
state['VALUE_CONSTANT'] = {value_constant}
state['CONSTANT_PROPERTIES'] = {constant_properties}
state['HOST_ID'] = '{host_id}'
"""

    QUERY_GET_DATA = "SELECT+{dimensions}+FROM+%22{metric}%22+WHERE+%22time%22+%3E%3D+${{record:value('/last_timestamp')}}+AND+%22time%22+%3C+${{record:value('/last_timestamp')}}%2B{interval}+AND+%22time%22+%3C+now%28%29-{delay}"
    QUERY_GET_TIMESTAMP = "SELECT+last_timestamp+FROM+agent_timestamps+WHERE+pipeline_id%3D%27${pipeline:id()}%27+ORDER+BY+time+DESC+LIMIT+1"
    QUERY_CHECK_DATA = "SELECT+{dimensions}+FROM+%22{metric}%22+WHERE+%22time%22+%3E+${{record:value('/last_timestamp_value')}}+AND+%22time%22+%3C+now%28%29-{delay}+ORDER+BY+time+ASC+limit+1"

    def get_write_client(self):
        host, db, username, password = self.get_write_config()
        influx_url_parsed = urlparse(host)
        influx_url = influx_url_parsed.netloc.split(':')
        args = {'database': db, 'host': influx_url[0], 'port': influx_url[1]}
        if username != '':
            args['username'] = username
            args['password'] = password
        if influx_url_parsed.scheme == 'https':
            args['ssl'] = True
        return InfluxDBClient(**args)

    def get_write_config(self):
        source_config = self.client_config['source']['config']
        if 'write_host' in source_config:
            host = source_config['write_host']
            db = source_config['write_db']
            username = source_config.get('write_username', '')
            password = source_config.get('write_password', '')
        else:
            host = source_config['host']
            db = source_config['db']
            username = source_config.get('username', '')
            password = source_config.get('password', '')
        return host, db, username, password

    def set_write_config_pipeline(self):
        host, db, username, password = self.get_write_config()
        config = {'host': host, 'db': db}
        if username != '':
            config['conf.client.authType'] = 'BASIC'
            config['conf.client.basicAuth.username'] = username
            config['conf.client.basicAuth.password'] = password
        return config

    def set_initial_offset(self):
        source_config = self.client_config['source']['config']
        if not source_config['offset']:
            source_config['offset'] = '0'

        if source_config['offset'].isdigit():
            timestamp = datetime.now() - timedelta(days=int(source_config['offset']))
        else:
            timestamp = datetime.strptime(source_config['offset'], '%d/%m/%Y %H:%M')

        source_config['offset'] = int(timestamp.timestamp() * 1e9)

        self.get_write_client().write_points([{
            'measurement': 'agent_timestamps',
            'tags': {'pipeline_id': self.client_config['pipeline_id']},
            'fields': {'last_timestamp': source_config['offset']}
        }])

    def override_stages(self):

        self.update_source_configs()

        for stage in self.config['stages']:

            if stage['instanceName'] == 'JavaScriptEvaluator_02':
                for conf in stage['configuration']:
                    if conf['name'] == 'stageRequiredFields':
                        conf['value'] = ['/' + d for d in self.client_config['dimensions']['required']]

                    if conf['name'] == 'initScript':
                        conf['value'] = self.DECLARE_VARS_JS.format(
                            required_dimensions=str(self.client_config['dimensions']['required']),
                            optional_dimensions=str(self.client_config['dimensions']['optional']),
                            measurement_name=self.client_config['measurement_name'],
                            values=str(self.client_config['value'].get('values', [])),
                            target_type=self.client_config.get('target_type', 'gauge'),
                            value_constant=self.client_config['value'].get('constant', '1'),
                            constant_properties=str(self.client_config.get('properties', {})),
                            host_id=self.client_config['destination']['host_id']
                        )

                    if conf['name'] == 'stageRecordPreconditions':
                        conf['value'] = []
                        for d in self.client_config['dimensions']['required']:
                            conf['value'].append(f"${{record:type('/{d}') == 'STRING'}}")
                        for d in self.client_config['dimensions']['optional']:
                            conf['value'].append(f"${{record:type('/{d}') == 'STRING' or record:type('/{d}') == NULL}}")
                        for v in self.client_config['value']['values']:
                            conf['value'].append(f"${{record:type('/{v}') != 'STRING'}}")

        self.update_destination_config()

    def update_source_configs(self):

        dimensions = self.get_dimensions()
        source_config = self.client_config['source']['config']
        dimensions_to_select = [f'%22{d}%22' + '%3A%3Atag' for d in dimensions]
        values_to_select = [f'%22{v}%22' + '%3A%3Afield' for v in self.client_config['value']['values']]
        username = source_config.get('username', '')
        password = source_config.get('password', '')
        if username != '':
            self.client_config['source']['config']['conf.client.authType'] = 'BASIC'
            self.client_config['source']['config']['conf.client.basicAuth.username'] = username
            self.client_config['source']['config']['conf.client.basicAuth.password'] = password

        delay = self.client_config.get('delay', '0s')
        interval = self.client_config.get('interval', 60)
        columns = ','.join(dimensions_to_select + values_to_select)
        self.set_initial_offset()

        source_config['conf.spoolingPeriod'] = interval
        source_config['conf.poolingTimeoutSecs'] = interval

        write_config = self.set_write_config_pipeline()

        for stage in self.config['stages']:
            if stage['instanceName'] == 'HTTPClient_03':
                query = f"/query?db={source_config['db']}&epoch=ns&q={self.QUERY_GET_DATA}".format(**{
                    'dimensions': columns,
                    'metric': self.client_config['measurement_name'],
                    'delay': delay,
                    'interval': str(interval) + 's',
                })
                self.update_http_stage(stage, self.client_config['source']['config'], urljoin(source_config['host'], query))

            if stage['instanceName'] == 'HTTPClient_04':
                get_timestamp_url = urljoin(write_config['host'],
                                            f"/query?db={write_config['db']}&epoch=ns&q={self.QUERY_GET_TIMESTAMP}")
                self.update_http_stage(stage, write_config, get_timestamp_url)

            if stage['instanceName'] == 'HTTPClient_05':
                self.update_http_stage(stage, write_config, urljoin(write_config['host'],
                                                      f"/write?db={write_config['db']}&precision=ns"))

            if stage['instanceName'] == 'HTTPClient_06':
                query = f"/query?db={source_config['db']}&epoch=ns&q={self.QUERY_CHECK_DATA}".format(**{
                    'dimensions': columns,
                    'metric': self.client_config['measurement_name'],
                    'delay': delay
                })
                self.update_http_stage(stage, self.client_config['source']['config'], urljoin(source_config['host'], query))

    def update_http_stage(self, stage, config, url=None):
        for conf in stage['configuration']:
            if conf['name'] == 'conf.resourceUrl' and url:
                conf['value'] = url
                continue

            if conf['name'] in config:
                conf['value'] = config[conf['name']]
