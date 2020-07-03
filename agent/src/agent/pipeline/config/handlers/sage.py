from .base import BaseConfigHandler
from agent.logger import get_logger
from agent.pipeline.config.stages import JSConvertMetrics, AddProperties, Destination, SageScript

logger = get_logger(__name__)


class SageConfigHandler(BaseConfigHandler):
    PIPELINE_BASE_CONFIG_NAME = 'sage_http.json'

    stages = {
        'source': SageScript,
        'JavaScriptEvaluator_01': JSConvertMetrics,
        'ExpressionEvaluator_02': AddProperties,
        'destination': Destination
    }

    def override_stages(self):
        self.pipeline.config['timestamp'] = {
            'name': '@timestamp',
            'type': 'string',
            'format': "yyyy-MM-dd\\'T\\'HH:mm:ss\\'Z\\'"
        }
        super().override_stages()