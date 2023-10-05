import subprocess  # noqa: I001
import typing as t

import typer
from rich import progress

from config_keeper.commands.config import cli as config_cli
from config_keeper.commands.paths import cli as paths_cli
from config_keeper.commands.project import cli as project_cli
from config_keeper import config, console
from config_keeper import exceptions as exc
from config_keeper.sync_handler import SyncHandler
from config_keeper.validation import ProjectValidator

cli = typer.Typer()

cli.add_typer(project_cli, name='project', help='Manage projects.')
cli.add_typer(config_cli, name='config', help='Manage config of this tool.')
cli.add_typer(paths_cli, name='paths', help='Manage project paths.')


@cli.command()
def push(
    projects: t.List[str],  # noqa: UP006
    ask: t.Annotated[bool, typer.Option()] = True,
):
    """
    Push files or directories of projects to their repositories. This operation
    is NOT atomic (i.e. failing operation for some project does not prevent
    other projects to be processed).
    """

    conf = config.load()

    validator = ProjectValidator(path_existence='error')
    for project in projects:
        validator.validate(project, conf)

    if ask:
        console.print('Following branches will most likely be overwritten:')

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
    ask: t.Annotated[bool, typer.Option()] = True,
):
    """
    Pull all files and directories of projects from their repositories and move
    them to projects' paths with complete overwrite of original files. This
    operation is NOT atomic (i.e. failing operation for some project does not
    prevent other projects to be processed).
    """

    conf = config.load()

    validator = ProjectValidator(path_existence='skip')
    for project in projects:
        validator.validate(project, conf)

    if ask:
        console.print('Following paths will most likely be replaced:')

        for project in projects:
            for path in conf['projects'][project]['paths'].values():
                console.print(f'- {path} (from "{project}")')

        if not typer.confirm('Proceed?', default=True):
            raise typer.Exit

    _operate('pull', projects, conf)


def _operate(
    operation: t.Literal['push', 'pull'],
    projects: list[str],
    conf: config.TConfig,
):
    errors: dict[str, str] = {}

    with progress.Progress() as p:
        task = p.add_task('Processing...', total=len(projects))
        for project in projects:
            handler = SyncHandler(project, conf)
            try:
                getattr(handler, operation)()
            except subprocess.CalledProcessError as e:
                errors[project] = e.stderr
            finally:
                p.update(task, advance=1)

    if errors:
        raise exc.SyncError(errors)

    console.print('Operation successfully completed.')
