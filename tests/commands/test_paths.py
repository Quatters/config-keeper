from config_keeper import config
from config_keeper.commands.paths import path_arg_regex

from tests.helpers import create_dir, create_file, invoke


def _test_config() -> config.TConfig:
    return {
        'projects': {
            'test1': {
                'branch': 'custom',
                'paths': {
                    'test_dir': str(create_dir()),
                    'test_file': str(create_file()),
                },
                'repository': 'invalid/repo',
            },
        },
    }


def test_path_arg_regex():
    assert path_arg_regex.match('valid:~/arg/любой язык.test')
    assert path_arg_regex.match('my_config.ini:~/arg/любой язык.test')
    assert path_arg_regex.match('my_config 2.ini:~/arg/любой язык.test')


def test_add():
    # non-existing project
    result = invoke([
        'paths', 'add', '--project', 'non-existing', 'some:some/path',
    ])
    assert result.exit_code == 203
    assert result.stdout == 'Error: project "non-existing" does not exist.\n'

    current_config = _test_config()
    config.save(current_config)

    # invalid argument format
    result = invoke([
        'paths', 'add', '--project', 'test1', 'invalid_arg::',
    ])
    assert result.exit_code == 205
    assert 'Error: invalid_arg:: is an invalid argument.' in result.stdout
    assert 'Format must be as follows:' in result.stdout
    assert 'path_name:/path/to/file/or/folder' in result.stdout
    assert config.load() == current_config

    some_file = create_file()
    another_file = create_file()

    # duplicate argument
    result = invoke([
        'paths', 'add', '--project', 'test1', f'some:{some_file}',
        f'some:{another_file}',
    ])
    assert result.exit_code == 207
    assert result.stdout == (
        'Error: path name "some" is repeated multiple times.\n'
    )
    assert config.load() == current_config

    # already in project
    result = invoke([
        'paths', 'add', '--project', 'test1', f'test_file:{some_file}',
        f'some:{another_file}',
    ])
    assert result.exit_code == 208
    assert result.stdout == (
        'Error: path name "test_file" already in "test1".\n'
        'Tip: you can use --overwrite option.\n'
    )
    assert config.load() == current_config

    # use --overwrite
    result = invoke([
        'paths', 'add', '--project', 'test1', f'test_file:{some_file}',
        f'some:{another_file}', '--overwrite',
    ])
    assert result.exit_code == 0
    assert result.stdout == 'Project "test1" saved.\n'

    # check changes
    current_config['projects']['test1']['paths']['test_file'] = str(some_file)
    current_config['projects']['test1']['paths']['some'] = str(another_file)
    assert config.load() == current_config


def test_delete():
    # non-existing project
    result = invoke([
        'paths', 'add', '--project', 'non-existing', 'some:some/path',
    ])
    assert result.exit_code == 203
    assert result.stdout == 'Error: project "non-existing" does not exist.\n'

    current_config = _test_config()
    config.save(current_config)

    # --no-ignore-missing
    result = invoke([
        'paths', 'delete', '--project', 'test1', 'test_dir', 'invalid',
    ])
    assert result.exit_code == 209
    assert result.stdout == (
        'Error: project "test1" does not have path named "invalid".\n'
        'Tip: you can use --ignore-missing option to suppress these errors.\n'
    )
    assert config.load() == current_config

    # --ignore-missing
    result = invoke([
        'paths', 'delete', '--project', 'test1', 'test_dir', 'invalid',
        '--ignore-missing',
    ])
    assert result.exit_code == 0
    assert result.stdout == 'Project "test1" saved.\n'

    # check changes
    del current_config['projects']['test1']['paths']['test_dir']
    assert config.load() == current_config
