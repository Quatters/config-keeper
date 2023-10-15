import functools
import os
import re
import subprocess
import typing as t
from pathlib import Path

from config_keeper import config
from config_keeper import exceptions as exc
from config_keeper.output import (
    print_critical,
    print_error,
    print_warning,
)

TYPENAME: dict[type, str] = {
    str: 'string',
    dict: 'map',
}


path_name_regex = re.compile(r'^[\w-]+$')
path_regex = re.compile(r'^[\w\/~\-\. ]+$')


def ping_remote(
    repository: str,
    *,
    capture: bool = False,
) -> subprocess.CompletedProcess[bytes] | subprocess.CompletedProcess[str]:
    cmd = ['git', 'ls-remote', repository, 'HEAD']
    if capture:
        return subprocess.run(cmd, check=True, capture_output=True, text=True)
    return subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )



def check_if_project_exists(project: str, conf: config.TConfig):
    if project not in conf['projects']:
        raise exc.ProjectDoesNotExistError(project)


def get_type(typehint: type) -> type:
    return getattr(typehint, '__origin__', typehint)


def find_not_accessible_parent(path: Path) -> Path | None:
    for parent in path.parents[::-1]:
        if not os.access(parent, os.X_OK):
            return parent
    return None  # nocv


def check_if_copyable(path: Path) -> tuple[bool, str]:
    if path.is_file():
        if not os.access(path, os.R_OK):
            return False, f'{path} has no read permission'
    elif path.is_dir():
        if not os.access(path, os.X_OK):
            return False, f'{path} has no execute permission'
    else:  # nocv
        raise ValueError(path)
    return True, ''


def check_if_writeable(path: Path) -> tuple[bool, str]:
    if not os.access(path, os.W_OK):
        return False, f'{path} has no write permission'
    return True, ''


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


RootReportType = t.Literal['unknown_param', 'type_mismatch']


class RootValidator(Validator):
    def __init__(
        self,
        conf: config.TConfig | dict[t.Any, t.Any],
        *,
        unknown_param: ReportLevel = 'warning',
        type_mismatch: ReportLevel = 'critical',
    ):
        super().__init__(conf)
        self.unknown_param = unknown_param
        self.type_mismatch = type_mismatch

    def validate(self) -> bool:
        for param, value in self.conf.items():
            if typehint := config.TConfigBound.__annotations__.get(param, None):
                realtype = get_type(typehint)
                if not isinstance(value, realtype):
                    self._report('type_mismatch', (
                        f'"{param}" is not a {TYPENAME[realtype]}.'
                    ))
            else:
                self._report('unknown_param', f'unknown parameter "{param}".')

        return self.is_valid

    def _report(self, report_type: RootReportType, msg: str):
        level: ReportLevel = getattr(self, report_type)
        getattr(self, f'_{level}')(msg)


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
    'not_copyable_path',
    'not_writeable_path',
    'path_parents_access',
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
        not_copyable_path: ReportLevel = 'error',
        not_writeable_path: ReportLevel = 'error',
        path_parents_access: ReportLevel = 'error',
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
        self.not_copyable_path = not_copyable_path
        self.not_writeable_path = not_writeable_path
        self.path_parents_access = path_parents_access

    def validate(self, project: str) -> bool:
        """
        Validates project config. Project must exist. After calling,
        ``.is_valid`` attribute shows either project is valid. Call
        ``print_errors`` to print all errors to stdout.
        """
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
        required_params = set(config.TProjectBound.__annotations__.keys())
        actual_params = set(self.conf['projects'][project].keys())
        for param in sorted(required_params - actual_params):
            self._report('missing_param', (
                f'"projects.{project}" missing parameter "{param}".'
            ))

    def _validate_param(
        self,
        param: str,
        value: t.Any,
        project: str,
    ):
        typehint = config.TProjectBound.__annotations__.get(param, None)
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
            self._report(f'empty_{param}', (  # type: ignore
                f'"projects.{project}.{param}" is empty.'
            ))
            return

        if param == 'repository':
            self._validate_repository(value, project)
        elif param == 'paths':
            for path_name, path in sorted(value.items()):
                self._validate_path(path_name, path, project)

    def _validate_path(self, path_name: str, path: t.Any, project: str):
        if not isinstance(path, str):
            self._report('type_mismatch', (
                f'"projects.{project}.paths.{path_name}" ({path}) is not a '
                f'{TYPENAME[str]}.'
            ))
            return
        if not path_name_regex.match(path_name):
            self._report('value_constraint', (
                f'"projects.{project}.paths.{path_name}" is not a valid path '
                'name.'
            ))
            return

        resolved_path = Path(path).expanduser().resolve()
        try:
            if not Path(resolved_path).exists():
                self._report('path_existence', (
                    f'"projects.{project}.paths.{path_name}" ({path}) does not '
                    'exist.'
                ))
                return
        except PermissionError:
            parent = find_not_accessible_parent(resolved_path)
            if parent is not None:
                self._report('path_parents_access', (
                    f'"projects.{project}.paths.{path_name}" is not '
                    f'accessible because {parent} has no execute permission.'
                ))
                return

        is_copyable, reason = check_if_copyable(resolved_path)
        if not is_copyable:
            self._report('not_copyable_path', (
                f'"projects.{project}.paths.{path_name}" is not '
                f'copyable because {reason}.'
            ))

        is_writable, reason = check_if_writeable(resolved_path)
        if not is_writable:
            self._report('not_writeable_path', (
                f'"projects.{project}.paths.{path_name}" is not '
                f'writeable because {reason}.'
            ))

    def _validate_repository(self, repository: t.Any, project: str):
        try:
            ping_remote(repository)
        except subprocess.CalledProcessError:
            self._report('repo_availability', (
                f'"projects.{project}.repository" ({repository}) is '
                'unavailable.'
            ))

    def _report(self, report_type: ProjectReportType, msg: str):
        level: ReportLevel = getattr(self, report_type)
        getattr(self, f'_{level}')(msg)
