import typing as t
from importlib import import_module
from pathlib import Path


class LazySettings:
    CONFIG_FILE: Path
    EXECUTABLE_NAME: str

    def __init__(self, settings_module: str):
        _super = super()
        _super.__setattr__('settings_module', import_module(settings_module))
        _super.__setattr__('real_settings', {
            key: getattr(self.settings_module, key)
            for key in dir(self.settings_module)
            if key.isupper()
        })
        _super.__setattr__('overridden_settings', {})

    def __getattr__(self, key: str) -> t.Any:
        return self.overridden_settings.get(key, self.real_settings[key])

    def __setattr__(self, key: str, value: t.Any):
        if key not in self.real_settings:  # nocv
            msg = f'{self.settings_module} has no attribute {key}'
            raise AttributeError(msg)
        self.overridden_settings[key] = value
