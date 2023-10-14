import typer

from config_keeper import config, settings
from config_keeper import exceptions as exc
from config_keeper.output import console
from config_keeper.progress import spinner
from config_keeper.validation import ProjectValidator, RootValidator

cli = typer.Typer()


@cli.command()
def path():
    """
    Show configuration file path. You can set CONFIG_KEEPER_CONFIG_FILE
    environment variable to change its path.
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
    has_warnings = False

    with spinner() as p:
        p.add_task('Validating...', total=None)

        root_validator = RootValidator(conf)
        is_valid = root_validator.validate()
        has_warnings = root_validator.has_warnings

        project_validator = ProjectValidator(conf, path_existence='warning')
        for project in conf['projects']:
            project_validator.validate(project)
            is_valid = is_valid and project_validator.is_valid
            has_warnings = has_warnings or project_validator.has_warnings

    root_validator.print_errors()
    project_validator.print_errors()

    if not is_valid:
        raise exc.InvalidConfigError

    if not has_warnings:
        console.print('OK', style='green')
