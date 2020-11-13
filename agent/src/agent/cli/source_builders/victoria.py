import click

from .abstract_builder import Builder
from agent.modules.tools import infinite_retry
from agent import source
from agent.modules import validator


class VictoriaSourceBuilder(Builder):
    def prompt(self, default_config, advanced=False):
        self.prompt_connection(default_config)
        self.prompt_verify_certificate(default_config, advanced)
        self.prompt_query_timeout(default_config, advanced)
        return self.source

    @infinite_retry
    def prompt_connection(self, default_config):
        self.prompt_url(default_config)
        self.prompt_username(default_config)
        self.prompt_password(default_config)

        self.validator.validate_connection()

    @infinite_retry
    def prompt_url(self, default_config):
        url = click.prompt('VictoriaMetrics API URL', type=click.STRING,
                           default=default_config.get(source.VictoriaMetricsSource.URL)).strip()
        try:
            validator.validate_url_format_with_port(url)
        except validator.ValidationException as e:
            raise click.ClickException(str(e))
        self.source.config[source.VictoriaMetricsSource.URL] = url

    def prompt_username(self, default_config):
        self.source.config['username'] = click.prompt('VictoriaMetrics username', type=click.STRING,
                                                      default=default_config.get('username', '')).strip()

    def prompt_password(self, default_config):
        self.source.config['password'] = click.prompt('VictoriaMetrics password', type=click.STRING,
                                                      default=default_config.get('password', '')).strip()

    def prompt_verify_certificate(self, default_config, advanced):
        verify = click.confirm('Verify ssl certificate?', default_config.get('verify_ssl', True)) if advanced else True
        self.source.config['verify_ssl'] = verify

    def prompt_query_timeout(self, default_config, advanced):
        if not advanced:
            return
        self.source.config['query_timeout'] = click.prompt('Query timeout (in seconds)', type=click.INT,
                                                           default=default_config.get('query_timeout', 15)).strip()
