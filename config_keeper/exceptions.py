import typer

from config_keeper import settings
from config_keeper.console_helpers import print_error, print_tip


class ConfigKeeperError(Exception):
    pass


class PublicError(typer.Exit, ConfigKeeperError):
    exit_code = 255  # default

    def __init__(self, msg: str | None = None, *, tip: str | None = None):
        if msg:
            print_error(msg)
        if tip:
            print_tip(tip)
        super(ConfigKeeperError, self).__init__(msg)


class InvalidConfigError(PublicError):
    exit_code = 201


class ProjectDoesNotExistError(PublicError):
    exit_code = 203
    message = 'project "{project}" does not exist.'

    def __init__(self, project: str, *, tip: str | None = None):
        self.project = project
        super().__init__(
            self.message.format(project=project),
            tip=tip,
        )


class AtLeastOneOptionMustBeProvidedError(PublicError):
    exit_code = 204

    def __init__(self, *, tip: str | None = None):
        super().__init__('at least one option must be provided.', tip=tip)


class InvalidArgumentFormatError(PublicError):
    exit_code = 205


class DuplicatePathNameError(PublicError):
    exit_code = 207

    def __init__(self, name: str, *, tip: str | None = None):
        super().__init__(
            f'path name "{name}" is repeated multiple times.',
            tip=tip,
        )


class PathNameAlreadyInProjectError(PublicError):
    exit_code = 208

    def __init__(self, name: str, project: str, *, tip: str | None = None):
        super().__init__(
            f'path name "{name}" already in "{project}".',
            tip=tip,
        )


class PathNameDoesNotExistError(PublicError):
    exit_code = 209

    def __init__(self, name: str, project: str, *, tip: str | None = None):
        super().__init__(
            f'project "{project}" does not have path named "{name}".',
            tip=tip,
        )


class SyncError(PublicError):
    exit_code = 220

    def __init__(self, errors_map: dict[str, str]):
        msg = 'operation failed for following projects:\n\n'

        for project, error in errors_map.items():
            msg += f'{project}\n'
            msg += '    ' + error.replace('\n', '\n    ') + '\n'

        super().__init__(msg)


class ExecutableNotFoundError(PublicError):
    exit_code = 254

    def __init__(self, executable: str):
        super().__init__(
            f'executable "{executable}" is not found in your system. '
            f'It is required for {settings.EXECUTABLE_NAME} to work correctly.',
        )
