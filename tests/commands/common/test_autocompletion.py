from click.core import Command as ClickCommand
from config_keeper import config
from config_keeper.commands.common import autocompletion

_test_conf = {
    'projects': {
        'test1': {
            'branch': 'main',
            'repository': 'does/not/matter',
            'paths': {
                'somefile': 'does/not/matter',
                'another_file': 'does/not/matter',
            },
        },
        'test2': {
            'branch': 'main',
            'repository': 'does/not/matter',
            'paths': {
                '1': 'does/not/matter',
                '12': 'does/not/matter',
            },
        },
        'other name': {
            'branch': 'main',
            'repository': 'does/not/matter',
            'paths': {
                'somefile': 'does/not/matter',
                'somefile2': 'does/not/matter',
            },
        },
    },
}


def get_context() -> autocompletion.Context:
    return autocompletion.Context(ClickCommand('update'))


def test_invalid_config():
    config.save({'projects': 'invalid'})
    ctx = get_context()

    autocompletion.project.__always_load__ = True
    assert autocompletion.project('', ctx) == []


def test_project():
    config.save(_test_conf)
    ctx = get_context()

    autocompletion.project.__always_load__ = True
    assert autocompletion.project('', ctx) == [
        'other name',
        'test1',
        'test2',
    ]
    assert autocompletion.project('te', ctx) == ['test1', 'test2']
    assert autocompletion.project('o', ctx) == ['other name']
    assert autocompletion.project('not found', ctx) == []


def test_path_name():
    config.save(_test_conf)
    ctx = get_context()
    autocompletion.path_name.__always_load__ = True

    # no project provided
    assert autocompletion.path_name('some', ctx) == []

    # project test1
    ctx.params = {'project': 'test1'}
    assert autocompletion.path_name('some', ctx) == ['somefile']

    # project test2
    ctx.params = {'project': 'test2'}
    assert autocompletion.path_name('1', ctx) == ['1', '12']


def test_lazy_conf():
    config.save(_test_conf)
    ctx = get_context()

    conf = None
    @autocompletion._lazy_config
    def some(incomplete: str, ctx: autocompletion.Context):
        nonlocal conf
        conf = ctx.conf

    # first call should trigger config.load()
    some('', ctx)
    assert conf == _test_conf

    # second call should not trigger config.load()
    config.save({'projects': {}})
    some('', ctx)
    assert conf == _test_conf
