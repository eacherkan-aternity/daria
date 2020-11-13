from .base import Stage


class Destination(Stage):
    def get_config(self) -> dict:
        return {
            'conf.agentOffsetUrl': self.pipeline.streamsets.agent_external_url + '/pipeline-offset/${pipeline:id()}'
        }


class WatermarkDestination(Stage):
    def get_config(self) -> dict:
        return self.pipeline.destination.config


class EventsDestination(Stage):
    def get_config(self) -> dict:
        return self.pipeline.destination.config
