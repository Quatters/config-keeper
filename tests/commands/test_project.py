from config_keeper import config, settings

from tests.helpers import create_repo, invoke

test_config = {
    'projects': {
        'test1': {
            'branch': 'custom',
            'paths': {},
            'repository': 'invalid/repo',
        },
        'test2': {
            'branch': 'main',
            'paths': {},
            'repository': 'another/repo',
        },
    },
}


def test_create():
    repo = create_repo()
    invalid_repo = 'invalid/repo'

    # check with prompts
    result = invoke(['project', 'create', 'test1'], input=f'{repo}\n\n')
    assert result.exit_code == 0, result.stdout
    assert 'Repository:' in result.stdout
    assert 'Branch [main]:' in result.stdout
    assert 'Checking' in result.stdout
    assert 'OK' in result.stdout
    assert 'Project "test1" saved.' in result.stdout
    assert config.load() == {
        'projects': {
            'test1': {
                'repository': str(repo),
                'branch': 'main',
                'paths': {},
            },
        },
    }

    # check with options
    result = invoke([
        'project', 'create', 'test1', f'--repository={invalid_repo}',
        '--branch=custom',
    ], input='y\ny\n')
    assert result.exit_code == 0, result.stdout
    assert 'Checking' in result.stdout
    assert 'Error:' in result.stderr
    assert 'Do you want to continue? [y/N]:' in result.stdout
    assert 'Project "test1" already exists.' in result.stdout
    assert 'Would you like to overwrite it? [y/N]:' in result.stdout
    assert 'Project "test1" saved.' in result.stdout
    assert config.load() == {
        'projects': {
            'test1': {
                'repository': str(invalid_repo),
                'branch': 'custom',
                'paths': {},
            },
        },
    }

    # check abort overwriting
    result = invoke([
        'project', 'create', 'test1', f'--repository={repo}',
        '--branch=new',
    ], input='n\n')
    assert result.exit_code == 0, result.stdout
    assert 'Checking' in result.stdout
    assert 'OK' in result.stdout
    assert 'Project "test1" already exists.' in result.stdout
    assert 'Would you like to overwrite it? [y/N]:' in result.stdout
    assert config.load() == {
        'projects': {
            'test1': {
                'repository': str(invalid_repo),
                'branch': 'custom',
                'paths': {},
            },
        },
    }

    # check --no-check
    result = invoke([
        'project', 'create', 'test2', f'--repository={invalid_repo}',
        '--branch=some', '--no-check',
    ], input='y\ny\n')
    assert result.exit_code == 0, result.stdout
    assert result.stdout == 'Project "test2" saved.\n'
    assert config.load() == {
        'projects': {
            'test1': {
                'repository': str(invalid_repo),
                'branch': 'custom',
                'paths': {},
            },
            'test2': {
                'repository': str(invalid_repo),
                'branch': 'some',
                'paths': {},
            },
        },
    }


def test_update():
    # non-existing project
    result = invoke(['project', 'update', 'some', '--repository=some'])
    assert result.exit_code == 203
    assert result.stderr == 'Error: project "some" does not exist.\n'

    config.save(test_config)

    # update without args
    result = invoke(['project', 'update', 'test1'])
    assert result.exit_code == 204
    assert result.stderr == 'Error: at least one option must be provided.\n'

    # valid update
    result = invoke(['project', 'update', 'test1', '--branch', 'new'])
    assert result.exit_code == 0
    assert result.stdout == 'Project "test1" saved.\n'

    # update repository
    repo = create_repo()
    result = invoke([
        'project', 'update', 'test1', '--repository', str(repo),
    ])
    assert result.exit_code == 0
    assert 'Checking' in result.stdout
    assert 'OK' in result.stdout
    assert 'Project "test1" saved.' in result.stdout

    # update repository (exit)
    result = invoke([
        'project', 'update', 'test1', '--repository', 'invalid',
    ], input='n\n')
    assert result.exit_code == 0
    assert result.stdout.startswith('Checking invalid...')
    assert 'Error:' in result.stderr
    assert result.stdout.endswith('Do you want to continue? [y/N]: n\n')


def test_delete():
    # check non-existing
    result = invoke(['project', 'delete', 'non-existing'])
    assert result.exit_code == 203
    assert result.stderr == 'Error: project "non-existing" does not exist.\n'

    config.save(test_config)

    # not confirm
    result = invoke(['project', 'delete', 'test1'], input='n\n')
    assert result.exit_code == 0
    assert result.stdout == (
        'You are about delete the following project:\n\n'
        'test1:\n'
        '  branch: custom\n'
        '  paths: {}\n'
        '  repository: invalid/repo\n\n'
        'Proceed? [Y/n]: n\n'
    )
    assert config.load() == test_config

    # confirm
    result = invoke(['project', 'delete', 'test1'], input='y\n')
    assert result.exit_code == 0
    assert result.stdout == (
        'You are about delete the following project:\n\n'
        'test1:\n'
        '  branch: custom\n'
        '  paths: {}\n'
        '  repository: invalid/repo\n\n'
        'Proceed? [Y/n]: y\n'
        'Project "test1" deleted.\n'
    )
    assert config.load() == {
        'projects': {
            'test2': {
                'branch': 'main',
                'paths': {},
                'repository': 'another/repo',
            },
        },
    }

    # use --no-confirm
    result = invoke(['project', 'delete', 'test2', '--no-confirm'])
    assert result.exit_code == 0
    assert result.stdout == (
        'Project "test2" deleted.\n'
    )
    assert config.load() == {'projects': {}}


def test_show():
    # check non-existing project
    result = invoke(['project', 'show', 'non-existing'])
    assert result.exit_code == 203
    assert result.stderr == 'Error: project "non-existing" does not exist.\n'

    config.save(test_config)

    result = invoke(['project', 'show', 'test1'])
    assert result.exit_code == 0
    assert result.stdout == (
        'test1:\n'
        '  branch: custom\n'
        '  paths: {}\n'
        '  repository: invalid/repo\n\n'
    )


def test_list():
    # no projects
    result = invoke(['project', 'list'])
    assert result.exit_code == 0
    assert result.stdout == (
        'You have no projects. Create a new one using\n'
        f'> {settings.EXECUTABLE_NAME} project create\n'
    )

    config.save(test_config)

    result = invoke(['project', 'list'])
    assert result.exit_code == 0
    assert result.stdout == (
        'test1\n'
        'test2\n'
    )

    # verbose
    result = invoke(['project', 'list', '-v'])
    assert result.exit_code == 0
    assert result.stdout == (
        'test1:\n'
        '  branch: custom\n'
        '  paths: {}\n'
        '  repository: invalid/repo\n'
        'test2:\n'
        '  branch: main\n'
        '  paths: {}\n'
        '  repository: another/repo\n\n'
    )
