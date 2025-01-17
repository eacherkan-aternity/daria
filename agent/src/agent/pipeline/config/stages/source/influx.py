from agent.pipeline.config.stages.base import Stage
from agent import pipeline
from urllib.parse import urljoin, quote_plus


class InfluxSource(Stage):
    QUERY_GET_DATA = "SELECT+{dimensions}+FROM+{metric}+WHERE+%28%22time%22+%3E%3D+${{record:value('/last_timestamp')}}+AND+%22time%22+%3C+${{record:value('/last_timestamp')}}%2B{interval}+AND+%22time%22+%3C+now%28%29+-+{delay}%29+{where}"

    def _get_config(self) -> dict:
        source_config = self.pipeline.source.config
        params = f"/query?db={source_config['db']}&epoch=ms&q="
        return {
            'conf.resourceUrl': urljoin(source_config['host'], params + self.get_query()),
            **self.get_auth_config()
        }

    def get_auth_config(self):
        if 'username' not in self.pipeline.source.config:
            return {}

        return {
            'conf.client.authType': 'BASIC',
            'conf.client.basicAuth.username': self.pipeline.source.config['username'],
            'conf.client.basicAuth.password': self.pipeline.source.config.get('password', '')
        }

    def get_query(self):
        if isinstance(self.pipeline, pipeline.TestPipeline):
            return f"select+%2A+from+{self.pipeline.config['measurement_name']}+limit+{pipeline.manager.MAX_SAMPLE_RECORDS}"

        dimensions_to_select = [f'"{d}"::tag' for d in self.pipeline.dimensions_names]
        values_to_select = ['*::field' if v == '*' else f'"{v}"::field' for v in self.pipeline.values]
        delay = self.pipeline.config.get('delay', '0s')
        columns = quote_plus(','.join(dimensions_to_select + values_to_select))

        where = self.pipeline.config.get('filtering')
        where = f'AND+%28{quote_plus(where)}%29' if where else ''

        measurement_name = self.pipeline.config['measurement_name']
        if '.' not in measurement_name and ' ' not in measurement_name:
            measurement_name = f'%22{measurement_name}%22'

        return self.QUERY_GET_DATA.format(**{
            'dimensions': columns,
            'metric': measurement_name,
            'delay': delay,
            'interval': str(self.pipeline.config.get('interval', 60)) + 's',
            'where': where
        })
