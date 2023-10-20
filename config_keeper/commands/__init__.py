import importlib.metadata  # noqa: I001
import typing as t

import typer

from config_keeper.commands.common import autocompletion, helps, sync
from config_keeper.commands.config import cli as config_cli
from config_keeper.commands.paths import cli as paths_cli
from config_keeper.commands.project import cli as project_cli
from config_keeper import config, settings
from config_keeper.output import console

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
projects_help = """
    List of project names.
"""
ref_help = """
    Commit sha or branch name to operate with. Only available if specified
    exactly one project. If not given than project branch is used.
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
    projects: t.Annotated[
        t.List[str],  # noqa: UP006
        typer.Argument(
            help=projects_help,
            autocompletion=autocompletion.projects,
        ),
    ],
    ask: t.Annotated[bool, typer.Option(help=ask_help)] = True,
    ref: t.Annotated[
        t.Optional[str],  # noqa: UP007
        typer.Option(help=ref_help),
    ] = None,
    verbose: t.Annotated[
        bool,
        typer.Option('--verbose', '-v', help=helps.verbose),
    ] = False,
):
    """
    Push files or directories of projects to their repositories. This operation
    is NOT atomic (i.e. failing operation for some project does not prevent
    other projects to be processed).
    """

    sync.check_options(projects, ask, ref)
    conf = config.load()
    validator = sync.get_validator('push', conf)
    sync.validate_projects(projects, validator)

    if ref:
        conf['projects'][projects[0]]['branch'] = ref

    sync.handle_push_ask(projects, conf, ask=ask)
    sync.operate('push', projects, conf, verbose)


@cli.command()
def pull(
    projects: t.Annotated[
        t.List[str],  # noqa: UP006
        typer.Argument(
            help=projects_help,
            autocompletion=autocompletion.projects,
        ),
    ],
    ask: t.Annotated[bool, typer.Option(help=ask_help)] = True,
    ref: t.Annotated[
        t.Optional[str],  # noqa: UP007
        typer.Option(help=ref_help),
    ] = None,
    verbose: t.Annotated[
        bool,
        typer.Option('--verbose', '-v', help=helps.verbose),
    ] = False,
):
    """
    Pull all files and directories of projects from their repositories and move
    them to projects' paths with complete overwrite of original files. This
    operation is NOT atomic (i.e. failing operation for some project does not
    prevent other projects to be processed).
    """

    sync.check_options(projects, ask, ref)
    conf = config.load()
    validator = sync.get_validator('pull', conf)
    sync.validate_projects(projects, validator)

    if ref:
        conf['projects'][projects[0]]['branch'] = ref

    sync.handle_pull_ask(projects, conf, ask=ask)
    sync.operate('pull', projects, conf, verbose)
