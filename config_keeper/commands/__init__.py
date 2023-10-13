import subprocess  # noqa: I001
import typing as t
import importlib.metadata

import typer

from config_keeper.commands.config import cli as config_cli
from config_keeper.commands.paths import cli as paths_cli
from config_keeper.commands.project import cli as project_cli
from config_keeper import config, console, settings
from config_keeper import exceptions as exc
from config_keeper.sync_handler import SyncHandler
from config_keeper.validation import ProjectValidator, check_if_project_exists
from config_keeper.progress import spinner

if t.TYPE_CHECKING:
    from rich.progress import TaskID

cli = typer.Typer(
    name=settings.EXECUTABLE_NAME,
    help='CLI tool for keeping your personal config files in a repository',
    pretty_exceptions_show_locals=False,
)

cli.add_typer(project_cli, name='project', help='Manage projects.')
cli.add_typer(config_cli, name='config', help='Manage config of this tool.')
cli.add_typer(paths_cli, name='paths', help='Manage project paths.')

ask_help = """
    Ask confirmation before operating.
"""

@cli.callback(invoke_without_command=True)
def print_version(
    version: t.Annotated[
        bool,
        typer.Option(
            '--version',
            help='Show current version and exit.',
            is_eager=True,
        ),
    ] = False,
):
    if version:
        console.print(
            importlib.metadata.version('config-keeper2'),
            highlight=False,
        )
        raise typer.Exit


@cli.command()
def push(
    projects: t.List[str],  # noqa: UP006
    ask: t.Annotated[bool, typer.Option(help=ask_help)] = True,
):
    """
    Push files or directories of projects to their repositories. This operation
    is NOT atomic (i.e. failing operation for some project does not prevent
    other projects to be processed).
    """

    conf = config.load()
    validator = ProjectValidator(
        conf,
        path_existence='error',
        not_copyable_path='error',
        not_writeable_path='skip',
    )

    _validate_projects(projects, validator)

    if ask:
        console.print('Going to push into following branches:')

        for project in projects:
            console.print(
                f'- "{conf["projects"][project]["branch"]}" at '
                f'{conf["projects"][project]["repository"]} '
                f'(from "{project}")',
            )

        if not typer.confirm('Proceed?', default=True):
            raise typer.Exit

    _operate('push', projects, conf)


@cli.command()
def pull(
    projects: t.List[str],  # noqa: UP006
    ask: t.Annotated[bool, typer.Option(help=ask_help)] = True,
):
    """
    Pull all files and directories of projects from their repositories and move
    them to projects' paths with complete overwrite of original files. This
    operation is NOT atomic (i.e. failing operation for some project does not
    prevent other projects to be processed).
    """

    conf = config.load()
    validator = ProjectValidator(
        conf,
        path_existence='skip',
        not_copyable_path='skip',
        not_writeable_path='error',
    )

    _validate_projects(projects, validator)

    if ask:
        console.print('Following paths will most likely be replaced:')

        for project in projects:
            for path in conf['projects'][project]['paths'].values():
                console.print(f'- {path} (from "{project}")')

        if not typer.confirm('Proceed?', default=True):
            raise typer.Exit

    _operate('pull', projects, conf)


def _validate_projects(
    projects: list[str],
    validator: ProjectValidator,
):
    for project in projects:
        check_if_project_exists(project, validator.conf)

    with spinner() as s:
        prev_task: TaskID | None = None
        for project in projects:
            if prev_task is not None:
                s.stop_task(prev_task)
            prev_task = s.add_task(
                f'Validating project "{project}"...',
                total=None,
            )
            validator.validate(project)

    validator.print_errors()
    if not validator.is_valid:
        raise exc.InvalidConfigError


def _operate(
    operation: t.Literal['push', 'pull'],
    projects: list[str],
    conf: config.TConfig,
):
    errors: dict[str, str] = {}

    with spinner() as s:
        prev_task: TaskID | None = None
        for project in projects:
            if prev_task is not None:
                s.stop_task(prev_task)
            prev_task = s.add_task(
                f'Processing project "{project}"...',
                total=None,
            )
            handler = SyncHandler(project, conf)
            try:
                getattr(handler, operation)()
            except subprocess.CalledProcessError as e:
                errors[project] = e.stdout + e.stderr

    if errors:
        raise exc.SyncError(errors)

    console.print('Operation successfully completed.')
