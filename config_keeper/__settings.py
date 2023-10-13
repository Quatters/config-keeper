import os
from pathlib import Path

import typer

# paths
_DEFAULT_CONFIG_FILE = (
    Path(typer.get_app_dir('config-keeper', roaming=False)) / 'config.yaml'
)
CONFIG_FILE = Path(os.getenv('CONFIG_KEEPER_CONFIG_FILE', _DEFAULT_CONFIG_FILE))

# etc
EXECUTABLE_NAME = 'config-keeper'
