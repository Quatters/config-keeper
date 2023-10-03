import os
from pathlib import Path

# paths
_DEFAULT_CONFIG_FILE = Path.home() / '.config-keeper.yaml'
CONFIG_FILE = Path(os.getenv('CONFIG_KEEPER_CONFIG_FILE', _DEFAULT_CONFIG_FILE))

# etc
EXECUTABLE_NAME = 'config-keeper'
