import re
import typing as t
from pathlib import Path

import typer

from config_keeper import config
from config_keeper import exceptions as exc
from config_keeper.commands.common import autocompletion, helps
from config_keeper.output import print_project_saved
from config_keeper.validation import check_if_project_exists

cli = typer.Typer()


path_arg_regex = re.compile(r'(^[\w\-\. ]+):([\w\/~\-\. ]+$)')

overwrite_help = """
    If set, overwrite path names if project already has them. Fail otherwise.
"""
paths_help = """
    Path list with following syntax: path_name:/path/to/file/or/dir. Path names
    of each project must be unique as it will be used as temporary file
    (directory) name for storing it in repository. Path after colon is any
    path to file (directory) in your filesystem.
"""
path_names_help = """
    Path names of project.
"""
ignore_missing_help = """
    If set, path names that are not exist in project will be ignored. Fail
    otherwise.
"""


@cli.command()
def add(
    project: t.Annotated[
        str,
        typer.Option(
            help=helps.project,
            autocompletion=autocompletion.project,
        ),
    ],
    paths: t.Annotated[
        t.List[str],  # noqa: UP006
        typer.Argument(help=paths_help),
    ],
    overwrite: t.Annotated[bool, typer.Option(help=overwrite_help)] = False,
):
    """
    Add directories or files to project. They will be pushed to (and pulled
    from) repository.
    """

    conf = config.load()
    check_if_project_exists(project, conf)

    new_paths = {}

    for raw_path in paths:
        match_ = path_arg_regex.match(raw_path)
        if not match_:
            msg = (
                f'{raw_path} is an invalid argument. Format must be as '
                'follows: path_name:/path/to/file/or/folder'
            )
            raise exc.InvalidArgumentFormatError(msg)
        key = match_.group(1)
        path = Path(match_.group(2))
        if key in new_paths:
            raise exc.DuplicatePathNameError(key)
        if key in conf['projects'][project]['paths'] and not overwrite:
            raise exc.PathNameAlreadyInProjectError(
                key,
                project,
                tip='you can use --overwrite option.',
            )
        new_paths[key] = str(path.expanduser().resolve())

    conf['projects'][project]['paths'].update(new_paths)
    config.save(conf)
    print_project_saved(project)


@cli.command()
def delete(
    project: t.Annotated[
        str,
        typer.Option(
            help=helps.project,
            autocompletion=autocompletion.project,
        ),
    ],
    path_names: t.Annotated[
        t.List[str],   # noqa: UP006
        typer.Argument(
            help=path_names_help,
            autocompletion=autocompletion.path_names,
        ),
    ],
    ignore_missing: t.Annotated[
        bool,
        typer.Option(help=ignore_missing_help),
    ] = False,
):
    """
    Delete paths by their path names from project. This will not affect original
    files or directories.
    """

    conf = config.load()
    check_if_project_exists(project, conf)

    for name in path_names:
        try:
            del conf['projects'][project]['paths'][name]
        except KeyError as e:
            if ignore_missing:
                continue
            raise exc.PathNameDoesNotExistError(
                name,
                project,
                tip=(
                    'you can use --ignore-missing option to suppress these '
                    'errors.'
                ),
            ) from e

    config.save(conf)
    print_project_saved(project)
