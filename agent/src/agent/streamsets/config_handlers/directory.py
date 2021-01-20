from agent.modules.logger import get_logger
from agent.pipeline.config import stages
from agent.streamsets.config_handlers.schema import SchemaConfigHandler

logger = get_logger(__name__)


class DirectoryConfigHandler(SchemaConfigHandler):
    stages_to_override = {
        'source': stages.source.Source,
        'JavaScriptEvaluator_01': stages.js_convert_metrics_20.JSConvertMetrics,
        'ExpressionEvaluator_02': stages.expression_evaluator.AddProperties30,
        'ExpressionEvaluator_03': stages.expression_evaluator.Filtering,
        'process_finish_file_event': stages.expression_evaluator.SendWatermark,
        'destination': stages.destination.Destination,
        'destination_watermark': stages.destination.WatermarkDestination,
    }