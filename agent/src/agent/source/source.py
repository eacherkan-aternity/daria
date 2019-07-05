import os
import json

from agent.constants import DATA_DIR


from .influx import PromptInflux
from .kafka import PromptKafka
from .mongo import PromptMongo


class Source:
    DIR = os.path.join(DATA_DIR, 'sources')

    TYPE_INFLUX = 'influx'
    TYPE_KAFKA = 'kafka'
    TYPE_MONGO = 'mongo'
    TYPE_MONITORING = 'Monitoring'

    types = [TYPE_INFLUX, TYPE_KAFKA, TYPE_MONGO]

    prompters = {
        TYPE_INFLUX: PromptInflux,
        TYPE_KAFKA: PromptKafka,
        TYPE_MONGO: PromptMongo
    }

    def __init__(self, name, source_type=None):
        self.config = {'name': name, 'type': source_type, 'config': {}}

    @property
    def file_path(self):
        return os.path.join(self.DIR, self.config['name'] + '.json')

    def exists(self):
        return os.path.isfile(self.file_path)

    def load(self):
        if not self.exists():
            raise SourceNotExists(f"Source config {self.config['name']} doesn't exist")

        with open(self.file_path, 'r') as f:
            self.config = json.load(f)

        return self.config

    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.config, f)

    def create(self):
        if self.exists():
            raise SourceException(f"Source config {self.config['name']} already exists")

        self.save()

    def delete(self):
        if not self.exists():
            raise SourceNotExists(f"Source config {self.config['name']} doesn't exist")

        os.remove(self.file_path)

    def prompt(self, default_config=None, advanced=False):
        if not default_config:
            default_config = self.config['config']
        self.config['config'] = self.prompters[self.config['type']]().prompt(default_config, advanced)

    @classmethod
    def get_list(cls):
        configs = []
        for filename in os.listdir(cls.DIR):
            if filename.endswith('.json'):
                configs.append(filename.replace('.json', ''))
        return configs


class SourceException(Exception):
    pass


class SourceNotExists(SourceException):
    pass
