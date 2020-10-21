import os

ANODOT_API_URL = os.environ.get('ANODOT_API_URL', 'https://api.anodot.com')
ENV_PROD = True if os.environ.get('ENV_PROD') == 'true' else False

HOSTNAME = os.environ.get('HOSTNAME', 'agent')

STREAMSETS_PREVIEW_TIMEOUT = os.environ.get('STREAMSETS_PREVIEW_TIMEOUT', 30000)

MONITORING_SOURCE_NAME = 'monitoring'

VALIDATION_ENABLED = True if os.environ.get('VALIDATION_ENABLED') == 'true' else False

AGENT_URL = os.environ.get('AGENT_URL', 'http://anodot-agent')

# todo this constant is wrong
ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

AGENT_DB_HOST = os.environ.get('AGENT_DB_HOST', 'db')
AGENT_DB_USER = os.environ.get('AGENT_DB_USER', 'agent')
AGENT_DB_PASSWORD = os.environ.get('AGENT_DB_USER', 'agent')
AGENT_DB = os.environ.get('AGENT_DB', 'agent')
BACKUP_DIRECTORY = os.environ.get('BACKUP_DIRECTORY', '/usr/src/app/backup-data')