import re
import typing as t
from pathlib import Path

import typer

from config_keeper import config
from config_keeper import exceptions as exc
from config_keeper.console_helpers import print_project_saved
from config_keeper.validation import check_if_project_exists

cli = typer.Typer()


path_arg_regex = re.compile(r'(^[\w-]+):([\w\/~\-\. ]+$)')


@cli.command()
def add(
    project: t.Annotated[str, typer.Option()],
    paths: t.List[str],  # noqa: UP006
    overwrite: t.Annotated[bool, typer.Option()] = False,
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
                'follows:\n\n'
                'key:/path/to/file/or/folder'
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
    project: t.Annotated[str, typer.Option()],
    path_names: t.List[str],  # noqa: UP006
    ignore_missing: t.Annotated[bool, typer.Option()] = False,
):
    """
    Delete paths by their keys from project. This will not affect original
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
