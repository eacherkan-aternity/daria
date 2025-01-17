import click

from agent.cli.prompt.pipeline import Prompter


class VictoriaPrompter(Prompter):
    def prompt_config(self):
        self.prompt_query()
        self.prompt_aggregated_metric_name()
        self.prompt_days_to_backfill()
        self.prompt_interval()
        self.prompt_delay()
        self.config['timestamp'] = {}
        self.config['timestamp']['type'] = 'unix'
        self.prompt_static_dimensions()
        self.prompt_tags()

    def prompt_query(self):
        self.config['query'] = click.prompt('Query to export data from VictoriaMetrics', type=click.STRING,
                                            default=self.default_config.get('query'))

    def prompt_aggregated_metric_name(self):
        aggregated_metric_name = self.default_config.get('aggregated_metric_name')
        if aggregated_metric_name:
            self.config['aggregated_metric_name'] = aggregated_metric_name
        if self.advanced:
            self.config['aggregated_metric_name'] = \
                click.prompt('Aggregated metric name', type=click.STRING, default=aggregated_metric_name)
