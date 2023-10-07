import re
from uuid import uuid1

from config_keeper import config, settings

from tests.helpers import invoke


def test_path():
    assert not settings.CONFIG_FILE.is_file()
    result = invoke(['config', 'path'])
    assert result.stdout.replace('\n', '') == f'{settings.CONFIG_FILE}'
    assert settings.CONFIG_FILE.is_file()


def test_validate():
    # check defaults (should be valid)
    result = invoke(['config', 'validate'])
    assert result.exit_code == 0
    assert result.stdout == '\nOK\n'

    invalid_path = str(uuid1()).replace('-', '/')
    test_config = {
        'invalid_root_key': {},
        'projects': {
            'test1': {
                'invalid_project_key': 'some',
                'repository': 'invalid/repo',
                'paths': {
                    'some_path': invalid_path,
                    'invalid_path_type': {},
                },
            },
            'test2': {},
            'test3': {
                'repository': ['some/repo'],
                'branch': {},
                'paths': '',
            },
            'test4': {
                'branch': '',
                'paths': {},
            },
            'test5': {
                'paths': {
                    '%^&': '',
                },
            },
            'test6': 'not_map',
        },
    }
    config.save(test_config)

    result = invoke(['config', 'validate'])
    assert result.exit_code == 201
    assert result.stdout == (
        '\nWarning: unknown parameter "invalid_root_key".\n'
        'Warning: unknown parameter "projects.test1.invalid_project_key".\n'
        'Critical: "projects.test1.paths.invalid_path_type" ({}) is not a '
        'string.\n'
        f'Warning: "projects.test1.paths.some_path" ({invalid_path}) does not\n'
        'exist.\n'
        'Error: "projects.test1.repository" (invalid/repo) is unavailable.\n'
        'Error: "projects.test1" missing parameter "branch".\n'
        'Error: "projects.test2" missing parameter "branch".\n'
        'Error: "projects.test2" missing parameter "paths".\n'
        'Error: "projects.test2" missing parameter "repository".\n'
        'Critical: "projects.test3.branch" is not a string.\n'
        'Critical: "projects.test3.paths" is not a map.\n'
        'Critical: "projects.test3.repository" is not a string.\n'
        'Error: "projects.test4.branch" is empty.\n'
        'Warning: "projects.test4.paths" is empty.\n'
        'Error: "projects.test4" missing parameter "repository".\n'
        'Error: "projects.test5.paths.%^&" is not a valid path name.\n'
        'Error: "projects.test5" missing parameter "branch".\n'
        'Error: "projects.test5" missing parameter "repository".\n'
        'Critical: "projects.test6" is not a map.\n'
    )

    test_config = {'projects': ''}
    config.save(test_config)

    result = invoke(['config', 'validate'])
    assert result.exit_code == 201
    assert result.stdout == (
        '\nCritical: "projects" is not a map.\n'
    )


def test_config_is_not_a_valid_yaml():
    settings.CONFIG_FILE.write_text('%$%$# not valid yaml\n\n\n\n')

    result = invoke(['config', 'validate'])
    assert result.exit_code == 201
    assert 'Error:' in result.stdout
    assert 'is not a valid YAML file' in result.stdout
    assert 'Please fix or remove it.' in result.stdout
    assert 'Tip: you can use' in result.stdout
    assert f'> {settings.EXECUTABLE_NAME} config validate\n' in result.stdout
    assert 'after.' in result.stdout
    assert re.match((
        f'^Error: [\n\w\/\-]+\.yaml is not a valid YAML file\.\n'
        'Please fix or remove it\.\n'
        'Tip: you can use\n'
        f'> {settings.EXECUTABLE_NAME} config validate\n'
        'after\.\n$'
    ), result.stdout)


def test_config_root_is_not_a_map():
    settings.CONFIG_FILE.write_text('some_text')

    result = invoke(['config', 'validate'])
    assert result.exit_code == 201
    assert 'Error: the root object of' in result.stdout
    assert 'config must be a' in result.stdout
    assert 'map.' in result.stdout
    assert 'Please fix or remove config.' in result.stdout
    assert 'Tip: you can use' in result.stdout
    assert f'> {settings.EXECUTABLE_NAME} config validate' in result.stdout
    assert 'after.' in result.stdout
