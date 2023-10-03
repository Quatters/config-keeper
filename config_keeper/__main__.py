import os

from config_keeper.commands import cli

os.environ['GIT_TERMINAL_PROMPT'] = '0'

cli()
