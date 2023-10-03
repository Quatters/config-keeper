from config_keeper.lazy_settings import LazySettings

settings = LazySettings('config_keeper.__settings')


from config_keeper.console import console  # noqa: F401, E402
