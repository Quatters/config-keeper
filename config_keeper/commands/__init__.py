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

cli = typer.Typer(no_args_is_help=True)

cli.add_typer(project_cli, name='project', no_args_is_help=True)
cli.add_typer(config_cli, name='config', no_args_is_help=True)
cli.add_typer(paths_cli, name='paths', no_args_is_help=True)


@cli.command()
def push(projects: t.List[str]):  # noqa: UP006
    """
    Push files or directories of projects to their repositories. This operation
    is NOT atomic (i.e. failing operation for some project does not prevent
    other projects to be processed).
    """

    _operate('push', projects, ProjectValidator(path_existence='error'))


@cli.command()
def pull(projects: t.List[str]):  # noqa: UP006
    """
    Pull all files and directories of projects from their repositories and move
    them to projects' paths with complete overwrite of original files. This
    operation is NOT atomic (i.e. failing operation for some project does not
    prevent other projects to be processed).
    """

    _operate('pull', projects, ProjectValidator(path_existence='skip'))


def _operate(
    operation: t.Literal['push', 'pull'],
    projects: list[str],
    validator: ProjectValidator,
):
    conf = config.load()

    for project in projects:
        validator.validate(project, conf)

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
