import subprocess
import typing as t

import typer

from config_keeper import config
from config_keeper import exceptions as exc
from config_keeper.output import console
from config_keeper.progress import spinner
from config_keeper.sync_handler import SyncHandler
from config_keeper.validation import ProjectValidator, check_if_project_exists

if t.TYPE_CHECKING:
    from rich.progress import TaskID

TOperation = t.Literal['push', 'pull']


def check_options(
    projects: list[str],
    ask: bool = True,
    ref: str | None = None,
):
    if ref is not None and len(projects) > 1:
        msg = '--ref option cannot be used with multiple projects.'
        raise exc.InvalidArgumentError(msg)


def get_validator(
    operation: TOperation,
    conf: config.TConfig,
) -> ProjectValidator:
    if operation == 'push':
        return ProjectValidator(
            conf,
            path_existence='error',
            not_copyable_path='error',
            not_writeable_path='skip',
        )
    return ProjectValidator(
        conf,
        path_existence='skip',
        not_copyable_path='skip',
        not_writeable_path='error',
    )


def validate_projects(
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


def handle_push_ask(projects: list[str], conf: config.TConfig, *, ask: bool):
    if not ask:
        return

    console.print('Going to push into following branches:')

    for project in projects:
        console.print(
            f'- "{conf["projects"][project]["branch"]}" at '
            f'{conf["projects"][project]["repository"]} '
            f'(from "{project}")',
        )

    if not typer.confirm('Proceed?', default=True):
        raise typer.Exit


def handle_pull_ask(projects: list[str], conf: config.TConfig, *, ask: bool):
    if not ask:
        return

    console.print('Following paths will most likely be replaced:')

    for project in projects:
        for path in conf['projects'][project]['paths'].values():
            console.print(f'- {path} (from "{project}")')

    if not typer.confirm('Proceed?', default=True):
        raise typer.Exit


def operate(
    operation: TOperation,
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
