import subprocess
import typing as t

import typer
import yaml
from rich.control import Control

from config_keeper import config, settings
from config_keeper import exceptions as exc
from config_keeper.commands.common import autocompletion, helps
from config_keeper.output import console, print_error, print_project_saved
from config_keeper.validation import check_if_project_exists, ping_remote

cli = typer.Typer()


@cli.command()
def create(
    project: t.Annotated[str, typer.Argument(help=helps.project)],
    repository: t.Annotated[
        str,
        typer.Option(prompt=True, help=helps.repository),
    ],
    branch: t.Annotated[
        str,
        typer.Option(prompt=True, help=helps.branch),
    ] = 'main',
    check: t.Annotated[bool, typer.Option(help=helps.check)] = True,
):
    """
    Create a new project.
    """

    if check:
        _check_remote(repository)

    conf = config.load()

    if project in conf['projects'] and not typer.confirm(
        f'Project "{project}" already exists. '
        'Would you like to overwrite it?',
    ):
        raise typer.Exit

    conf['projects'][project] = {
        'repository': repository,
        'branch': branch,
        'paths': {},
    }
    config.save(conf)
    print_project_saved(project)


@cli.command()
def update(
    project: t.Annotated[
        str,
        typer.Argument(
            help=helps.project,
            autocompletion=autocompletion.project,
        ),
    ],
    repository: t.Annotated[
        t.Optional[str],  # noqa: UP007
        typer.Option(help=helps.repository),
    ] = None,
    branch: t.Annotated[
        t.Optional[str],  # noqa: UP007
        typer.Option(help=helps.branch),
    ] = None,
    check: t.Annotated[bool, typer.Option(help=helps.check)] = True,
):
    """
    Update project.
    """

    conf = config.load()
    check_if_project_exists(project, conf)

    updated = False
    data = conf['projects'][project]

    if repository:
        if check:
            _check_remote(repository)
        data['repository'] = repository
        updated = True

    if branch:
        data['branch'] = branch
        updated = True

    if not updated:
        raise exc.AtLeastOneOptionMustBeProvidedError

    config.save(conf)
    print_project_saved(project)


@cli.command()
def delete(
    project: t.Annotated[
        str,
        typer.Argument(
            help=helps.project,
            autocompletion=autocompletion.project,
        ),
    ],
    confirm: t.Annotated[
        bool,
        typer.Option(help='Whether confirm before deleting.'),
    ] = True,
):
    """
    Delete project.
    """

    conf = config.load()
    check_if_project_exists(project, conf)

    if confirm:
        console.print('You are about delete the following project:\n')
        console.print(yaml.dump({project: conf['projects'][project]}))
        if not typer.confirm('Proceed?', default=True):
            raise typer.Exit

    del conf['projects'][project]
    config.save(conf)
    console.print(f'Project "{project}" deleted.')


@cli.command()
def show(
    project: t.Annotated[
        str,
        typer.Argument(
            help=helps.project,
            autocompletion=autocompletion.project,
        ),
    ],
):
    """
    Show project config.
    """

    conf = config.load()
    check_if_project_exists(project, conf)

    info = {project: conf['projects'][project]}
    console.print(yaml.dump(info))


@cli.command(name='list')
def list_(
    verbose: t.Annotated[
        bool,
        typer.Option('--verbose', '-v', help=helps.verbose),
    ] = False,
):
    """
    List all projects.
    """

    conf = config.load()

    if not conf['projects']:
        console.print('You have no projects. Create a new one using')
        console.print(f'> {settings.EXECUTABLE_NAME} project create')
        raise typer.Exit

    if verbose:
        console.print(yaml.dump(conf['projects']))
    else:
        for project in conf['projects']:
            console.print(project)


@cli.command()
def rename(
    old_project: t.Annotated[
        str,
        typer.Argument(
            help=helps.project,
            autocompletion=autocompletion.project,
        ),
    ],
    new_project: t.Annotated[
        str,
        typer.Argument(help=helps.project),
    ],
):
    """
    Rename existing project.
    """

    if old_project == new_project:
        msg = 'specify a different name.'
        raise exc.InvalidArgumentError(msg)

    conf = config.load()
    check_if_project_exists(old_project, conf)

    if new_project in conf['projects']:
        raise exc.ProjectAlreadyExistsError(new_project)

    conf['projects'][new_project] = conf['projects'].pop(old_project)
    config.save(conf)

    print_project_saved(new_project)


def _check_remote(repository: str):
    msg = f'Checking {repository}...'
    console.print(msg)
    try:
        ping_remote(repository, capture=True)
        console.control(Control.move(y=-1, x=len(msg)+1))
        console.print('OK', style='green')
    except subprocess.CalledProcessError as exc:
        msg = exc.stdout + exc.stderr
        msg = '\n    ' + msg.replace('\n', '\n    ')
        print_error(msg)
        if not typer.confirm('Do you want to continue?'):
            raise typer.Exit from exc
