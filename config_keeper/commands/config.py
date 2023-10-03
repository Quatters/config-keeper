import typer

from config_keeper import config, console, settings
from config_keeper import exceptions as exc
from config_keeper.console_helpers import print_critical, print_warning
from config_keeper.validation import TYPENAME, ProjectValidator, get_type

cli = typer.Typer()


@cli.command()
def path():
    """
    Show configuration file path.
    """

    config.ensure_exists()
    console.print(settings.CONFIG_FILE)


@cli.command()
def validate():
    """
    Validate config for missing or unknown params, check repositories and paths.
    """

    conf = config.load()
    is_valid = True

    for key, value in conf.items():
        if typehint := config.TConfig.__annotations__.get(key, None):
            realtype = get_type(typehint)
            if not isinstance(value, realtype):
                print_critical(f'"{key}" is not a {TYPENAME[realtype]}.')
                is_valid = False
        else:
            print_warning(f'unknown parameter "{key}".')

    validator = ProjectValidator(path_existence='warning')
    for project in conf['projects']:
        try:
            validator.validate(project, conf)
        except exc.InvalidConfigError:
            is_valid = False

    if not is_valid:
        raise exc.InvalidConfigError

    console.print('Config is valid.')
