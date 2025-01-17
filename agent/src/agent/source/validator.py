import json
import os
import urllib.parse
import jsonschema
import requests
import inject

from abc import ABC, abstractmethod
from datetime import datetime
from urllib.parse import urlparse
from agent import source
from agent.modules.tools import if_validation_enabled
from agent.modules import validator, zabbix
from agent.source import Source


def validate(source_: Source):
    get_validator(source_).validate()


class IConnectionValidator(ABC):
    @staticmethod
    @abstractmethod
    def validate(source_: Source):
        pass


class Validator:
    VALIDATION_SCHEMA_FILE = ''
    connection_validator = inject.attr(IConnectionValidator)

    def __init__(self, source_: Source):
        self.source = source_

    def validate(self):
        self.validate_json()
        self.validate_connection()

    def validate_json(self):
        file_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'json_schema_definitions', self.VALIDATION_SCHEMA_FILE
        )
        with open(file_path) as f:
            json_schema = json.load(f)
        jsonschema.validate(self.source.config, json_schema)

    @if_validation_enabled
    def validate_connection(self):
        self.connection_validator.validate(self.source)


class InfluxValidator(Validator):
    VALIDATION_SCHEMA_FILE = 'influx.json'

    def validate(self):
        super().validate()
        self.validate_db()
        self.validate_offset()

    @if_validation_enabled
    def validate_connection(self):
        try:
            validator.validate_url_format_with_port(self.source.config['host'])
        except validator.ValidationException as e:
            raise ValidationException(str(e))
        client = source.db.get_influx_client(self.source.config['host'])
        client.ping()

    @if_validation_enabled
    def validate_db(self):
        client = source.db.get_influx_client(self.source.config['host'], self.source.config.get('username'),
                                             self.source.config.get('password'))
        if not any([db['name'] == self.source.config['db'] for db in client.get_list_database()]):
            raise ValidationException(
                f"Database {self.source.config['db']} not found. Please check your credentials again"
            )

    def validate_offset(self):
        if not self.source.config.get('offset'):
            return

        if self.source.config['offset'].isdigit():
            try:
                int(self.source.config['offset'])
            except ValueError:
                raise ValidationException(self.source.config['offset'] + ' is not a valid integer')
        else:
            try:
                datetime.strptime(self.source.config['offset'], '%d/%m/%Y %H:%M').timestamp()
            except ValueError as e:
                raise ValidationException(str(e))


class ElasticValidator(Validator):
    VALIDATION_SCHEMA_FILE = 'elastic.json'

    @if_validation_enabled
    def validate_connection(self):
        # todo
        self.source.config[source.ElasticSource.CONFIG_IS_INCREMENTAL] = False
        super().validate_connection()


class JDBCValidator(Validator):
    VALIDATION_SCHEMA_FILE = 'jdbc.json'

    def validate(self):
        self.validate_json()
        self.validate_connection_string()
        self.validate_connection()

    @if_validation_enabled
    def validate_connection_string(self):
        try:
            validator.validate_url_format_with_port(self.source.config[source.JDBCSource.CONFIG_CONNECTION_STRING])
        except validator.ValidationException as e:
            raise ValidationException(str(e))
        result = urlparse(self.source.config[source.JDBCSource.CONFIG_CONNECTION_STRING])
        if self.source.type == source.TYPE_MYSQL and result.scheme != 'mysql':
            raise ValidationException('Wrong url scheme. Use `mysql`')
        if self.source.type == source.TYPE_POSTGRES and result.scheme != 'postgresql':
            raise ValidationException('Wrong url scheme. Use `postgresql`')
        if self.source.type == source.TYPE_CLICKHOUSE and result.scheme != 'clickhouse':
            raise ValidationException('Wrong url scheme. Use `clickhouse`')


class MongoValidator(Validator):
    VALIDATION_SCHEMA_FILE = 'mongo.json'

    def validate(self):
        super().validate()
        self.validate_db()
        self.validate_collection()

    @if_validation_enabled
    def validate_connection(self):
        client = source.db.get_mongo_client(
            self.source.config[source.MongoSource.CONFIG_CONNECTION_STRING],
            self.source.config.get(source.MongoSource.CONFIG_USERNAME),
            self.source.config.get(source.MongoSource.CONFIG_PASSWORD),
            self.source.config.get(source.MongoSource.CONFIG_AUTH_SOURCE)
        )
        client.server_info()

    @if_validation_enabled
    def validate_db(self):
        client = source.db.get_mongo_client(
            self.source.config[source.MongoSource.CONFIG_CONNECTION_STRING],
            self.source.config.get(source.MongoSource.CONFIG_USERNAME),
            self.source.config.get(source.MongoSource.CONFIG_PASSWORD),
            self.source.config.get(source.MongoSource.CONFIG_AUTH_SOURCE)
        )
        if self.source.config[source.MongoSource.CONFIG_DATABASE] not in client.list_database_names():
            raise ValidationException(
                f'Database {self.source.config[source.MongoSource.CONFIG_DATABASE]} doesn\'t exist')

    @if_validation_enabled
    def validate_collection(self):
        client = source.db.get_mongo_client(
            self.source.config[source.MongoSource.CONFIG_CONNECTION_STRING],
            self.source.config.get(source.MongoSource.CONFIG_USERNAME),
            self.source.config.get(source.MongoSource.CONFIG_PASSWORD),
            self.source.config.get(source.MongoSource.CONFIG_AUTH_SOURCE)
        )
        if self.source.config[source.MongoSource.CONFIG_COLLECTION] \
                not in client[self.source.config[source.MongoSource.CONFIG_DATABASE]].list_collection_names():
            raise ValidationException(
                f'Collection {self.source.config[source.MongoSource.CONFIG_DATABASE]} doesn\'t exist')


class SageValidator(Validator):
    VALIDATION_SCHEMA_FILE = 'sage.json'

    def validate(self):
        self.validate_json()
        self.validate_url()
        self.validate_token()

    @if_validation_enabled
    def validate_url(self):
        try:
            validator.validate_url_format(self.source.config[source.SageSource.URL])
        except validator.ValidationException as e:
            raise ValidationException(str(e))
        # TODO: check simple request

    @if_validation_enabled
    def validate_token(self):
        # TODO: check token
        pass


class VictoriaMetricsValidator(Validator):
    VALIDATION_SCHEMA_FILE = 'victoria.json'

    def validate_connection(self):
        url = self.source.config['url'] + '/api/v1/export?match[]={__name__="not_existing_dsger43"}'
        session = requests.Session()
        if self.source.config.get(source.VictoriaMetricsSource.USERNAME):
            session.auth = (
                self.source.config[source.VictoriaMetricsSource.USERNAME],
                self.source.config[source.VictoriaMetricsSource.PASSWORD]
            )
        try:
            res = session.get(url, verify=False)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ValidationException(
                'Failed connecting to VictoriaMetrics. Make sure you provided correct url, username and password\n'
                + str(e)
            )


class SolarWindsValidator(Validator):
    VALIDATION_SCHEMA_FILE = 'solarwinds.json'

    def validate_connection(self):
        url = urllib.parse.urljoin(
            self.source.config['url'],
            '/SolarWinds/InformationService/v3/Json/Query?query=SELECT+TOP+1+1+as+test+FROM+Orion.Accounts'
        )
        session = requests.Session()
        session.auth = (
            self.source.config[source.APISource.USERNAME],
            self.source.config[source.APISource.PASSWORD]
        )
        try:
            res = session.get(url, verify=False, timeout=20)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ValidationException(
                'Failed to connect to SolarWinds. Make sure you provided correct url, API username and password:\n'
                + str(e)
            )


class ZabbixValidator(Validator):
    VALIDATION_SCHEMA_FILE = 'zabbix.json'

    def validate_connection(self):
        zabbix.Client(
            self.source.config[source.ZabbixSource.URL],
            self.source.config[source.ZabbixSource.USER],
            self.source.config[source.ZabbixSource.PASSWORD],
        )


class SchemalessValidator(Validator):
    def validate(self):
        super().validate()
        self.validate_grok_file()

    def validate_grok_file(self):
        if self.source.config.get(source.SchemalessSource.CONFIG_GROK_PATTERN_FILE) and not os.path.isfile(
                self.source.config[source.SchemalessSource.CONFIG_GROK_PATTERN_FILE]):
            raise ValidationException('File does not exist')


class KafkaValidator(SchemalessValidator):
    VALIDATION_SCHEMA_FILE = 'kafka.json'


class SplunkValidator(SchemalessValidator):
    VALIDATION_SCHEMA_FILE = 'tcp_server.json'


class DirectoryValidator(SchemalessValidator):
    VALIDATION_SCHEMA_FILE = 'directory.json'


class CactiValidator(Validator):
    VALIDATION_SCHEMA_FILE = 'cacti.json'

    def validate(self):
        super().validate()
        validator.file_exists(self.source.config[source.CactiSource.RRD_ARCHIVE_PATH])

    @if_validation_enabled
    def validate_connection(self):
        validator.validate_mysql_connection(self.source.config[source.CactiSource.MYSQL_CONNECTION_STRING])


class ValidationException(Exception):
    pass


def get_validator(source_: Source) -> Validator:
    types = {
        source.TYPE_CACTI: CactiValidator,
        source.TYPE_CLICKHOUSE: JDBCValidator,
        source.TYPE_DIRECTORY: DirectoryValidator,
        source.TYPE_ELASTIC: ElasticValidator,
        source.TYPE_INFLUX: InfluxValidator,
        source.TYPE_KAFKA: KafkaValidator,
        source.TYPE_MONGO: MongoValidator,
        source.TYPE_MYSQL: JDBCValidator,
        source.TYPE_POSTGRES: JDBCValidator,
        source.TYPE_SAGE: SageValidator,
        source.TYPE_SPLUNK: SplunkValidator,
        source.TYPE_SOLARWINDS: SolarWindsValidator,
        source.TYPE_VICTORIA: VictoriaMetricsValidator,
        source.TYPE_ZABBIX: ZabbixValidator,
    }
    return types[source_.type](source_)
