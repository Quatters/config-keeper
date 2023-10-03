import typing as t

import yaml

from config_keeper import settings


class TProject(t.TypedDict):
    repository: str
    branch: str
    paths: dict[str, str]


class TConfig(t.TypedDict):
    projects: dict[str, TProject]


def defaults() -> t.Callable[[], TConfig]:
    return {
        'projects': {},
    }


def ensure_exists():
    settings.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    settings.CONFIG_FILE.touch()


def load() -> TConfig:
    ensure_exists()
    from config_keeper import exceptions as exc
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
            f'you can use\n> {settings.EXECUTABLE_NAME} config validate\n'
            'after.'
        )
        raise exc.InvalidConfigError(msg, tip=tip) from e
    if config is None:
        return defaults()
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
    return config


def save(config: TConfig):
    raw = yaml.dump(config)
    settings.CONFIG_FILE.write_text(raw)
