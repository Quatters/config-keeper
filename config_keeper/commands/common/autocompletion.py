import functools
import typing as t

import typer

from config_keeper import config
from config_keeper import exceptions as exc


class Context(typer.Context):
    conf: config.TConfig


TCompleteFuncReturn = list[str]
TCompleteFunc = t.Callable[[str, Context], TCompleteFuncReturn]


def _lazy_config(func: TCompleteFunc) -> TCompleteFunc:
    """
    Decorator which loads config only on first call of decorated function. If
    config is invalid then defaults used. Decorated function must take ``ctx``
    argument, in which ``conf`` attribute contains config.
    """
    conf: config.TConfig | None = None

    @functools.wraps(func)
    def wrapper(incomplete: str, ctx: Context) -> TCompleteFuncReturn:
        nonlocal conf
        if conf is None or getattr(wrapper, '__always_load__', False):
            try:
                conf = config.load()
            except exc.InvalidConfigError:
                conf = {}
                config.populate_defaults(conf)
        ctx.conf = conf
        return func(incomplete, ctx)

    return wrapper


@_lazy_config
def project(incomplete: str, ctx: Context) -> TCompleteFuncReturn:
    completions: list[str] = []
    for project in ctx.conf['projects']:
        if project.startswith(incomplete):
            completions.append(project)
    return completions


@_lazy_config
def projects(incomplete: str, ctx: Context) -> TCompleteFuncReturn:
    completions: list[str] = []
    used_projects = ctx.params.get('projects') or ()
    for project in ctx.conf['projects']:
        if project not in used_projects and project.startswith(incomplete):
            completions.append(project)
    return completions


@_lazy_config
def path_names(incomplete: str, ctx: Context) -> TCompleteFuncReturn:
    project = ctx.params.get('project')
    if project:
        paths = ctx.conf['projects'].get(project, {}).get('paths')
        if isinstance(paths, dict):
            all_completions = [str(path) for path in paths]
            used_paths = ctx.params.get('path_names') or ()
            return [
                path
                for path in all_completions
                if path not in used_paths and path.startswith(incomplete)
            ]
    return []
