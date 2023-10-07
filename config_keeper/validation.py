import functools
import re
import subprocess
import typing as t
from pathlib import Path

from config_keeper import config
from config_keeper import exceptions as exc
from config_keeper.console_helpers import (
    print_critical,
    print_error,
    print_warning,
)

TYPENAME: dict[type[type], str] = {
    str: 'string',
    dict: 'map',
}


path_name_regex = re.compile(r'^[\w-]+$')
path_regex = re.compile(r'^[\w\/~\-\. ]+$')


def ping_remote(
    repository: str,
    *,
    log: bool = False,
) -> subprocess.CompletedProcess:
    kwargs = {'capture_output': True, 'text': True}
    if not log:
        kwargs = {'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}
    return subprocess.run(
        ['git', 'ls-remote', repository, 'HEAD'],
        check=True,
        **kwargs,
    )


def check_if_project_exists(project: str, conf: config.TConfig):
    if project not in conf['projects']:
        raise exc.ProjectDoesNotExistError(project)


def get_type(typehint: type[type] | t.GenericAlias) -> type[type]:
    return getattr(typehint, '__origin__', typehint)


ReportLevel = t.Literal['skip', 'warning', 'error', 'critical']


class Validator:
    def __init__(
        self,
        conf: config.TConfig,
    ):
        self.is_valid = True
        self.has_warnings = False
        self.conf = conf
        self._message_printers: list[t.Callable[[], None]] = []

    def print_errors(self):
        for printer in self._message_printers:
            printer()

    def _skip(self, _: str):
        pass

    def _warning(self, msg: str):
        self.has_warnings = True
        self._message_printers.append(functools.partial(print_warning, msg))

    def _error(self, msg: str):
        self.is_valid = False
        self._message_printers.append(functools.partial(print_error, msg))

    def _critical(self, msg: str):
        self.is_valid = False
        self._message_printers.append(functools.partial(print_critical, msg))

    def _report(self, report_type: str, msg: str):
        level: ReportLevel = getattr(self, report_type)
        getattr(self, f'_{level}')(msg)


RootReportType = t.Literal['unknown_param', 'type_mismatch']


class RootValidator(Validator):
    def __init__(
        self,
        conf: config.TConfig,
        *,
        unknown_param: ReportLevel = 'warning',
        type_mismatch: ReportLevel = 'critical',
    ):
        super().__init__(conf)
        self.unknown_param = unknown_param
        self.type_mismatch = type_mismatch

    def validate(self) -> bool:
        for param, value in self.conf.items():
            if typehint := config.TConfig.__annotations__.get(param, None):
                realtype = get_type(typehint)
                if not isinstance(value, realtype):
                    self._report('type_mismatch', (
                        f'"{param}" is not a {TYPENAME[realtype]}.'
                    ))
            else:
                self._report('unknown_param', f'unknown parameter "{param}".')

        return self.is_valid

    def _report(self, report_type: RootReportType, msg: str):
        super()._report(report_type, msg)


ProjectReportType = t.Literal[
    'path_existence',
    'repo_availability',
    'unknown_param',
    'missing_param',
    'empty_repository',
    'empty_branch',
    'empty_paths',
    'type_mismatch',
    'value_constraint',
]


class ProjectValidator(Validator):
    def __init__(
        self,
        conf: config.TConfig,
        *,
        path_existence: ReportLevel = 'error',
        repo_availability: ReportLevel = 'error',
        unknown_param: ReportLevel = 'warning',
        missing_param: ReportLevel = 'error',
        empty_repository: ReportLevel = 'error',
        empty_branch: ReportLevel = 'error',
        empty_paths: ReportLevel = 'warning',
        type_mismatch: ReportLevel = 'critical',
        value_constraint: ReportLevel = 'error',
    ):
        super().__init__(conf)
        self.path_existence = path_existence
        self.repo_availability = repo_availability
        self.unknown_param = unknown_param
        self.missing_param = missing_param
        self.empty_repository = empty_repository
        self.empty_branch = empty_branch
        self.empty_paths = empty_paths
        self.type_mismatch = type_mismatch
        self.value_constraint = value_constraint

    def validate(self, project: str) -> bool:
        check_if_project_exists(project, self.conf)

        if not isinstance(self.conf['projects'][project], dict):
            self._critical(
                f'"projects.{project}" is not a {TYPENAME[dict]}.',
            )
            return self.is_valid

        for param, value in sorted(self.conf['projects'][project].items()):
            self._validate_param(param, value, project)

        self._check_missing_params(project)

        return self.is_valid

    def _check_missing_params(self, project: str):
        required_params = set(config.TProject.__annotations__.keys())
        actual_params = set(self.conf['projects'][project].keys())
        for param in sorted(required_params - actual_params):
            self._report('missing_param', (
                f'"projects.{project}" missing parameter "{param}".'
            ))

    def _validate_param(
        self,
        param: str,
        value: t.Any,  # noqa: ANN401
        project: str,
    ):
        typehint = config.TProject.__annotations__.get(param, None)
        if not typehint:
            self._report('unknown_param', (
                f'unknown parameter "projects.{project}.{param}".'
            ))
            return

        realtype = get_type(typehint)
        if not isinstance(value, realtype):
            self._report('type_mismatch', (
                f'"projects.{project}.{param}" is not a {TYPENAME[realtype]}.'
            ))
            return

        if not value:
            self._report(f'empty_{param}', (
                f'"projects.{project}.{param}" is empty.'
            ))
            return

        if param == 'repository':
            self._validate_repository(value, project)
        elif param == 'paths':
            for path_name, path in sorted(value.items()):
                self._validate_path(path_name, path, project)

    def _validate_path(self, path_name: str, path: str, project: str):
        if not isinstance(path, str):
            self._report('type_mismatch', (
                f'"projects.{project}.paths.{path_name}" ({path}) is not a '
                f'{TYPENAME[str]}.'
            ))
        elif not path_name_regex.match(path_name):
            self._report('value_constraint', (
                f'"projects.{project}.paths.{path_name}" is not a valid path '
                'name.'
            ))
        elif not Path(path).exists():
            self._report('path_existence', (
                f'"projects.{project}.paths.{path_name}" ({path}) does not '
                'exist.'
            ))

    def _validate_repository(self, repository: str, project: str):
        try:
            ping_remote(repository)
        except subprocess.CalledProcessError:
            self._report('repo_availability', (
                f'"projects.{project}.repository" ({repository}) is '
                'unavailable.'
            ))

    def _report(self, report_type: ProjectReportType, msg: str):
        super()._report(report_type, msg)
