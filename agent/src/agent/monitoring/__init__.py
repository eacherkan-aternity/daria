import anodot

from . import metrics, streamsets
from agent.modules import constants, logger
from datetime import datetime
from prometheus_client import generate_latest

logger_ = logger.get_logger(__name__)


def get_latest():
    streamsets.get_metrics()
    return generate_latest(registry=metrics.registry)


def latest_to_anodot():
    get_latest()

    data = []
    for metric in metrics.registry.collect():
        target_type = anodot.TargetType.COUNTER if metric.type == 'counter' else anodot.TargetType.GAUGE
        for sample in metric.samples:

            if sample.name.endswith('_created'):
                continue
            dims = {**sample.labels, 'host_name': constants.HOSTNAME, 'source': 'agent_monitoring'}
            data.append(anodot.Metric20(sample.name, sample.value, target_type, datetime.now(),
                                        dimensions=dims).to_dict())

    return data
