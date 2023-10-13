import re
from uuid import uuid1

from config_keeper import config, settings

from tests.helpers import create_dir, create_file, create_repo, invoke


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
        'Critical: "projects" is not a map.\n'
    )


def test_validate_files_permissions():
    file_without_read_perm = create_file(
        name='file_without_read_perm',
    )
    file_without_write_perm = create_file(
        name='file_without_write_perm',
    )
    dir_without_write_perm = create_dir(
        name='dir_without_write_perm',
    )
    dir_without_exec_perm = create_dir(
        name='dir_without_exec_perm',
    )
    file_in_dir = create_file(
        parent=dir_without_exec_perm,
        name='file_in_dir',
    )

    file_without_read_perm.chmod(0o333)
    file_without_write_perm.chmod(0o444)
    dir_without_exec_perm.chmod(0o666)
    dir_without_write_perm.chmod(0o555)

    repo = create_repo()

    config.save({
        'projects': {
            'test1': {
                'branch': 'mybranch',
                'repository': str(repo),
                'paths': {
                    'file_without_read_perm': str(file_without_read_perm),
                    'file_without_write_perm': str(file_without_write_perm),
                    'file_in_dir': str(file_in_dir),
                    'dir_without_exec_perm': str(dir_without_exec_perm),
                    'dir_without_write_perm': str(dir_without_write_perm),
                },
            },
        },
    })

    result = invoke(['config', 'validate'])
    assert result.exit_code == 201
    formatted_stdout = result.stdout.replace('\n', ' ').replace('  ', ' ')

    # parse paths because if they are too long then in random place
    # \n char may appear
    # e.g. /long/path -> /long/p\nath
    replaced_stdout = re.sub(
        r'(\/[\w \/]+) has',
        '<path> has',
        formatted_stdout,
    )

    assert (
        'Error: "projects.test1.paths.file_without_read_perm" is not '
        'copyable because <path> has no read '
        'permission.'
    ) in replaced_stdout
    assert (
        'Error: "projects.test1.paths.file_in_dir" is not accessible '
        'because <path> has no execute permission.'
    ) in replaced_stdout
    assert (
        'Error: "projects.test1.paths.dir_without_exec_perm" is not '
        'copyable because <path> has no '
        'execute permission.'
    ) in replaced_stdout
    assert (
        'Error: "projects.test1.paths.file_without_write_perm" is not '
        'writeable because <path> has no write permission.'
    ) in replaced_stdout
    assert (
        'Error: "projects.test1.paths.dir_without_write_perm" is not writeable '
        'because <path> has no write permission.'
    ) in replaced_stdout

    # check paths separately
    path_strings = {
        s.replace(' has', '').replace(' ', '')
        for s in re.findall(r'(\/[\w \/]+) has', formatted_stdout)
    }
    assert str(file_without_read_perm) in path_strings
    assert str(file_in_dir.parent) in path_strings
    assert str(dir_without_exec_perm) in path_strings
    assert str(file_without_write_perm) in path_strings
    assert str(dir_without_write_perm) in path_strings


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
        rf'^Error: [\n\w\/\-]+\.yaml is not a valid YAML file\.\n'
        r'Please fix or remove it\.\n'
        'Tip: you can use\n'
        f'> {settings.EXECUTABLE_NAME} config validate\n'
        r'after\.\n$'
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


def test_config_projects_is_not_a_map():
    settings.CONFIG_FILE.write_text('projects: string')

    result = invoke(['config', 'validate'])
    assert result.exit_code == 201
    assert 'Critical: "projects" is not a map.' in result.stdout


def test_empty_config_is_valid():
    settings.CONFIG_FILE.write_text('{}')

    result = invoke(['config', 'validate'])
    assert result.exit_code == 0
    assert config.load() == {'projects': {}}


def test_oserror_for_config_file():
    somefile = create_file()
    somefile.chmod(0o333)
    settings.CONFIG_FILE = somefile

    result = invoke(['config', 'validate'])
    assert result.exit_code == 255
    assert 'Permission denied' in result.stdout

    somedir = create_dir()
    somedir.chmod(0o000)
    settings.CONFIG_FILE = somedir / 'somefile'
    result = invoke(['config', 'validate'])
    assert result.exit_code == 255
    assert 'Permission denied' in result.stdout
