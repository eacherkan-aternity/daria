from datetime import datetime
from agent import pipeline, source, destination

for pipeline_ in pipeline.repository.get_all():
    pipeline_.created_at = datetime.now()
    pipeline.repository.save(pipeline_)

for source_ in source.repository.get_all():
    source_.created_at = datetime.now()
    source.repository.save(source_)

destination_ = destination.repository.get()
destination_.created_at = datetime.now()
destination.repository.save(destination_)