import typing as t

import yaml

from config_keeper import exceptions as exc
from config_keeper import settings


class TProjectBound(t.TypedDict):
    repository: str
    branch: str
    paths: dict[str, str]


TProject = TProjectBound | dict[str, t.Any]


class TConfigBound(t.TypedDict):
    projects: dict[str, TProject]


TConfig = TConfigBound | dict[str, t.Any]


def populate_defaults(config: dict[str, t.Any]):
    for key, type_ in TConfigBound.__annotations__.items():
        config.setdefault(key, type_())


def ensure_exists():
    try:
        settings.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        settings.CONFIG_FILE.touch()
    except OSError as e:
        raise exc.PublicError(str(e)) from e


def load() -> TConfig:
    ensure_exists()
    try:
        config = yaml.load(
            settings.CONFIG_FILE.read_bytes(),
            Loader=yaml.Loader,
        )
    except yaml.error.YAMLError as e:
        msg = (
            f'{settings.CONFIG_FILE} is not a valid YAML file.\n'
            'Please fix or remove it.'
        )
        tip = (
            'you can use\n'
            f'> {settings.EXECUTABLE_NAME} config validate\n'
            'after.'
        )
        raise exc.InvalidConfigError(msg, tip=tip) from e
    except OSError as e:
        raise exc.PublicError(str(e)) from e

    config = config or {}

    if not isinstance(config, dict):
        msg = (
            f'the root object of {settings.CONFIG_FILE} config must be a map.\n'
            'Please fix or remove config.\n'
        )
        tip = (
            f'you can use\n> {settings.EXECUTABLE_NAME} config validate\n'
            'after.'
        )
        raise exc.InvalidConfigError(msg, tip=tip)

    populate_defaults(config)

    from config_keeper.validation import RootValidator
    validator = RootValidator(config, unknown_param='skip')
    is_valid = validator.validate()
    validator.print_errors()
    if not is_valid:
        raise exc.InvalidConfigError

    return config


def save(config: TConfig):
    raw = yaml.dump(config)
    settings.CONFIG_FILE.write_text(raw)
