from .source import *
from .source import Source
from . import repository
from . import manager
from . import validator
from . import db
from . import json_builder

TYPE_CACTI = 'cacti'
TYPE_CLICKHOUSE = 'clickhouse'
TYPE_DIRECTORY = 'directory'
TYPE_ELASTIC = 'elastic'
TYPE_INFLUX = 'influx'
TYPE_KAFKA = 'kafka'
TYPE_MONGO = 'mongo'
TYPE_MYSQL = 'mysql'
TYPE_POSTGRES = 'postgres'
TYPE_SAGE = 'sage'
TYPE_SPLUNK = 'splunk'
TYPE_SOLARWINDS = 'solarwinds'
TYPE_VICTORIA = 'victoria'
TYPE_ZABBIX = 'zabbix'

types = {
    TYPE_CACTI: CactiSource,
    TYPE_CLICKHOUSE: JDBCSource,
    TYPE_DIRECTORY: DirectorySource,
    TYPE_ELASTIC: ElasticSource,
    TYPE_INFLUX: InfluxSource,
    TYPE_KAFKA: KafkaSource,
    TYPE_MONGO: MongoSource,
    TYPE_MYSQL: JDBCSource,
    TYPE_POSTGRES: JDBCSource,
    TYPE_SAGE: SageSource,
    TYPE_SOLARWINDS: SolarWindsSource,
    TYPE_SPLUNK: TCPSource,
    TYPE_VICTORIA: VictoriaMetricsSource,
    TYPE_ZABBIX: ZabbixSource,
}

json_schema = {
    'type': 'object',
    'properties': {
        'type': {'type': 'string', 'enum': list(types.keys())},
        'name': {'type': 'string', 'minLength': 1, 'maxLength': 100},
        'config': {'type': 'object'}
    },
    'required': ['type', 'name', 'config']
}
