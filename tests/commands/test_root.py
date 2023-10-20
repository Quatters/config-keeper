import importlib.metadata
import subprocess
from unittest import mock
from uuid import uuid1

import pytest
from config_keeper import config, settings
from config_keeper import exceptions as exc
from config_keeper.sync_handler import (
    SyncHandler,
)
from config_keeper.sync_handler import (
    run_cmd as sync_handler_run_cmd,
)
from freezegun import freeze_time

from tests.helpers import create_dir, create_file, create_repo, invoke, run_cmd


def test_version():
    real_version = importlib.metadata.version('config-keeper2')
    result = invoke(['--version'])
    assert result.exit_code == 0, result.stdout
    assert result.stdout == f'{real_version}\n'


def test_push_creates_remote_branch():
    repo = create_repo()
    some_dir = create_dir()
    create_file(
        name='nested_file',
        parent=some_dir,
        content='nested file content',
    )
    some_file = create_file(content='some file content')

    config.save({
        'projects': {
            'test1': {
                'branch': 'my_branch',
                'repository': str(repo),
                'paths': {
                    'some_dir': str(some_dir),
                    'some_file': str(some_file),
                },
            },
        },
    })

    result = invoke(['push', 'test1', '--no-ask'])
    assert result.exit_code == 0
    assert result.stdout.endswith('Operation successfully completed.\n')

    run_cmd(['git', '-C', str(repo), 'checkout', 'my_branch'])

    assert (repo / 'some_file').is_file()
    assert (repo / 'some_file').read_text() == 'some file content'
    assert (repo / 'some_dir').is_dir()
    assert (repo / 'some_dir' / 'nested_file').is_file()
    assert (repo / 'some_dir' / 'nested_file').read_text() == (
        'nested file content'
    )


def test_push_overwrites_remote_branch_content():
    repo = create_repo()
    some_dir = create_dir(name='some_dir')
    create_file(
        name='nested_file',
        parent=some_dir,
        content='nested file content',
    )
    some_file = create_file(name='some_file', content='some file content')

    config.save({
        'projects': {
            'test1': {
                'branch': 'my_branch',
                'repository': str(repo),
                'paths': {
                    'some_dir': str(some_dir),
                    'some_file': str(some_file),
                },
            },
        },
    })

    run_cmd(['git', '-C', str(repo), 'checkout', '-b', 'my_branch'])

    # create same files and directory, create file which must be deleted
    create_file(
        name='some_file',
        parent=repo,
        content='old content',
    )
    create_file(name='must_be_deleted', parent=repo)
    create_file(
        name='nested_file',
        parent=create_dir(name='some_dir', parent=repo),
        content='old content',
    )
    # commit changes
    run_cmd(['git', '-C', str(repo), 'add', '.'])
    run_cmd(['git', '-C', str(repo), 'commit', '-m', 'some_message'])

    # checkout another branch in remote repo to avoid push error
    run_cmd(['git', '-C', str(repo), 'checkout', '-b', 'empty_branch'])
    result = invoke(['push', 'test1', '--no-ask'])
    assert result.exit_code == 0, result.stdout

    run_cmd(['git', '-C', str(repo), 'checkout', 'my_branch'])

    assert (repo / 'some_file').is_file()
    assert (repo / 'some_file').read_text() == 'some file content'
    assert (repo / 'some_dir').is_dir()
    assert (repo / 'some_dir' / 'nested_file').is_file()
    assert (repo / 'some_dir' / 'nested_file').read_text() == (
        'nested file content'
    )
    assert not (repo /  'must_be_deleted').exists()


def test_push_preserves_commit_history():
    repo = create_repo()
    some_file = create_file(name='some_file', content='some file content')

    config.save({
        'projects': {
            'test1': {
                'branch': 'my_branch',
                'repository': str(repo),
                'paths': {
                    'some_file': str(some_file),
                },
            },
        },
    })

    run_cmd(['git', '-C', str(repo), 'checkout', '-b', 'my_branch'])

    # create commit
    create_file(
        name='some_file',
        parent=repo,
        content='old content',
    )
    run_cmd(['git', '-C', str(repo), 'add', '.'])
    run_cmd(['git', '-C', str(repo), 'commit', '-m', 'some_message'])

    # checkout another branch in remote repo to avoid push error
    run_cmd(['git', '-C', str(repo), 'checkout', '-b', 'empty_branch'])

    # push
    result = invoke(['push', 'test1', '--no-ask'])
    assert result.exit_code == 0, result.stdout

    # checkout right branch
    run_cmd(['git', '-C', str(repo), 'checkout', 'my_branch'])

    # check commits
    result = run_cmd(['git', '-C', str(repo), 'log', '--pretty=oneline'])
    lines = [line for line in result.stdout.split('\n') if line != '']
    assert len(lines) == 2, lines
    assert 'Auto push' in lines[0]
    assert 'some_message' in lines[1]


def test_error_on_push():
    some_file = create_file()
    repo = create_repo()

    config.save({
        'projects': {
            'test1': {
                'branch': 'my_branch',
                'repository': str(repo),
                'paths': {
                    'some_file': str(some_file),
                },
            },
            'test2': {
                'branch': 'my_branch',
                'repository': str(repo),
                'paths': {
                    'some_file': str(some_file),
                },
            },
            'test3': {
                'branch': 'my_branch',
                'repository': str(repo),
                'paths': {
                    'some_file': str(some_file),
                },
            },
        },
    })

    def trouble_maker(
        self: SyncHandler,
        project: str,
        conf: config.TConfig,
        *,
        verbose_output: bool = False,
    ):
        if project in ('test1', 'test3'):
            conf['projects'][project]['repository'] = 'invalid/repo'
        self.project = project
        self.conf = conf
        self._output = ''
        self.verbose_output = verbose_output

    with mock.patch(
        'config_keeper.sync_handler.SyncHandler.__init__',
        side_effect=trouble_maker,
        autospec=True,
    ):
        result = invoke(['push', 'test1', 'test2', 'test3', '--no-ask'])
    assert result.exit_code == 220
    assert (
        'Error: operation did not succeeded for "test1", "test3".\n'
    ) in result.stderr
    assert 'test3' in result.stderr

    # check that test2 is successfully pushed
    run_cmd(['git', '-C', str(repo), 'checkout', 'my_branch'])
    assert (repo / 'some_file').is_file()


def test_push_with_ask():
    repo = create_repo()
    some_file = create_file(name='some_file', content='some file content')

    config.save({
        'projects': {
            'test1': {
                'branch': 'my_branch',
                'repository': str(repo),
                'paths': {
                    'some_file': str(some_file),
                },
            },
        },
    })

    result = invoke(['push', 'test1', '--ask'], input='n\n')
    assert result.exit_code == 0, result.stdout
    assert result.stdout.startswith(
        '\nGoing to push into following branches:',
    )
    assert '- "my_branch" at ' in result.stdout
    assert '(from "test1")' in result.stdout

    with pytest.raises(subprocess.CalledProcessError):
        run_cmd(['git', '-C', str(repo), 'checkout', 'my_branch'])

    # confirm ask
    result = invoke(['push', 'test1', '--ask'], input='y\n')
    assert result.exit_code == 0, result.stdout
    assert result.stdout.startswith(
        '\nGoing to push into following branches:',
    )
    assert '- "my_branch" at ' in result.stdout
    assert '(from "test1")' in result.stdout
    assert 'Proceed? [Y/n]: y' in result.stdout
    assert result.stdout.endswith('Operation successfully completed.\n')

    run_cmd(['git', '-C', str(repo), 'checkout', 'my_branch'])

    assert (repo / 'some_file').is_file()
    assert (repo / 'some_file').read_text() == 'some file content'


def test_sync_with_ref():
    repo = create_repo()
    some_file = create_file(name='some_file', content='some file content')

    conf = {
        'projects': {
            'test1': {
                'branch': 'non-existing-branch',
                'repository': str(repo),
                'paths': {
                    'some_file': str(some_file),
                },
            },
        },
    }
    config.save(conf)

    result = invoke(['push', 'test1', '--no-ask', '--ref', 'my_branch'])
    assert result.exit_code == 0
    assert 'Operation successfully completed.' in result.stdout

    # check that my_branch has pushed file
    run_cmd(['git', '-C', str(repo), 'checkout', 'my_branch'])
    assert (repo / 'some_file').is_file()
    assert (repo / 'some_file').read_text() == 'some file content'

    with pytest.raises(
        subprocess.CalledProcessError,
        match=r'^Command .+ returned non-zero exit status 1\.$',
    ):
        run_cmd(['git', '-C', str(repo), 'checkout', 'non-existing-branch'])

    # checkout another branch to not fail on next pushes
    run_cmd(['git', '-C', str(repo), 'checkout', '-b', 'empty'])

    # get commit sha
    result = run_cmd(['git', '-C', str(repo), 'log', '--pretty=format:%H'])
    first_commit_sha = result.stdout
    assert isinstance(first_commit_sha, str)

    # push another file
    another_file = create_file(name='another_file')
    conf['projects']['test1']['paths']['another_file'] = str(another_file)
    config.save(conf)

    result = invoke(['push', 'test1', '--no-ask', '--ref', 'my_branch'])
    assert result.exit_code == 0, result.stderr
    assert 'Operation successfully completed.' in result.stdout

    # delete files
    some_file.unlink()
    another_file.unlink()

    # pull specifying branch
    result = invoke(['pull', 'test1', '--no-ask', '--ref', 'my_branch'])
    assert result.exit_code == 0, result.stderr
    assert 'Operation successfully completed.' in result.stdout
    assert some_file.is_file()
    assert some_file.read_text() == 'some file content'
    assert another_file.is_file()

    # delete files again
    some_file.unlink()
    another_file.unlink()

    # pull specifying commit sha
    result = invoke(['pull', 'test1', '--no-ask', '--ref', first_commit_sha])
    assert result.exit_code == 0, result.stderr
    assert 'Skipped ' in result.stdout
    assert 'because repository does not' in result.stdout
    assert 'contain ./another_file' in result.stdout
    assert 'Operation successfully completed.' in result.stdout
    assert some_file.is_file()
    assert some_file.read_text() == 'some file content'
    assert not another_file.is_file()


@freeze_time('2000-01-01 00:00:00')
def test_commit_message():
    repo = create_repo()
    some_file = create_file(name='some_file', content='some file content')

    config.save({
        'projects': {
            'test1': {
                'branch': 'my_branch',
                'repository': str(repo),
                'paths': {
                    'some_file': str(some_file),
                },
            },
        },
    })

    result = invoke(['push', 'test1', '--no-ask'])
    assert result.exit_code == 0

    run_cmd(['git', '-C', str(repo), 'checkout', 'my_branch'])
    result = run_cmd(['git', '-C', str(repo), 'log', '--pretty=format:%s'])
    assert result.stdout == 'Auto push from 2000-01-01 00:00 [test1]'


def test_executable_not_found():
    executable = str(uuid1())
    with pytest.raises(
        exc.ExecutableNotFoundError,
        match=f'^executable "{executable}" is not found in your system. '
        f'It is required for {settings.EXECUTABLE_NAME} to work correctly.$',
    ):
        sync_handler_run_cmd([executable, 'some'])


def test_pull_overwrites_original_files():
    repo = create_repo()
    source_dir = create_dir()

    config.save({
        'projects': {
            'test1': {
                'repository': str(repo),
                'branch': 'my_branch',
                'paths': {
                    'some_file': str(source_dir  / 'some_file'),
                    'some_dir': str(source_dir  / 'some_dir'),
                    'some_nested_file': str(
                        source_dir /
                        'another_dir' /
                        'nested_file',
                    ),
                },
            },
        },
    })

    # fill repo
    run_cmd(['git', '-C', str(repo), 'checkout', '-b', 'my_branch'])

    (repo / 'some_file').write_text('some_content')
    (repo / 'some_dir').mkdir()
    (repo / 'some_dir' / 'some_dir_file').touch()
    (repo / 'some_nested_file').write_text('nested_content')

    run_cmd(['git', '-C', str(repo), 'add', '.'])
    run_cmd(['git', '-C', str(repo), 'commit', '-m', 'some message'])

    result = invoke(['pull', 'test1', '--no-ask'])
    assert result.exit_code == 0
    assert result.stdout.endswith('Operation successfully completed.\n')

    # check fetched files
    assert (source_dir  / 'some_file').is_file()
    assert (source_dir  / 'some_file').read_text() == 'some_content'
    assert (source_dir  / 'some_dir').is_dir()
    assert (source_dir  / 'some_dir' / 'some_dir_file').is_file()
    assert (source_dir  / 'another_dir' / 'nested_file').is_file()
    assert (source_dir  / 'another_dir' / 'nested_file').read_text() == (
        'nested_content'
    )

    # change files in repo
    (repo / 'some_file').write_text('new_content')
    (repo / 'some_dir' / 'some_dir_file').touch()
    (repo / 'some_nested_file').write_text('new_content')

    run_cmd(['git', '-C', str(repo), 'add', '.'])
    run_cmd(['git', '-C', str(repo), 'commit', '-m', 'some message'])

    # add file to some_dir which must be deleted after pull
    file_must_be_deleted = (source_dir / 'some_dir' / 'file_must_be_deleted')
    file_must_be_deleted.touch()

    result = invoke(['pull', 'test1', '--no-ask'])
    assert result.exit_code == 0
    assert result.stdout.endswith('Operation successfully completed.\n')

    assert not file_must_be_deleted.exists()
    assert (source_dir / 'some_file').read_text() == 'new_content'
    assert (source_dir / 'another_dir' / 'nested_file').read_text() == (
        'new_content'
    )
    assert (source_dir / 'some_dir' / 'some_dir_file').is_file()


def test_pull_creates_file_if_it_not_exists():
    repo = create_repo()
    dest = create_dir()

    config.save({
        'projects': {
            'test1': {
                'repository': str(repo),
                'branch': 'my_branch',
                'paths': {
                    'somedir': str(dest / 'somedir'),
                    'somefile': str(dest / 'somefile'),
                },
            },
        },
    })

    run_cmd(['git', '-C', str(repo), 'checkout', '-b', 'my_branch'])

    (repo / 'somefile').touch()
    (repo / 'somedir').mkdir()
    (repo / 'somedir' / 'somefile2').touch()

    run_cmd(['git', '-C', str(repo), 'add', '.'])
    run_cmd(['git', '-C', str(repo), 'commit', '-m', 'some message'])

    result = invoke(['pull', 'test1', '--no-ask'])
    assert result.exit_code == 0, result.stderr

    assert (dest / 'somefile').is_file()
    assert (dest / 'somedir').is_dir()
    assert (dest / 'somedir' / 'somefile2').is_file()


def test_pull_with_ask():
    repo = create_repo()
    source_dir = create_dir()

    config.save({
        'projects': {
            'test1': {
                'repository': str(repo),
                'branch': 'my_branch',
                'paths': {
                    'some_file': str(source_dir  / 'some_file'),
                },
            },
        },
    })

    run_cmd(['git', '-C', str(repo), 'checkout', '-b', 'my_branch'])

    (repo / 'some_file').write_text('some_content')

    run_cmd(['git', '-C', str(repo), 'add', '.'])
    run_cmd(['git', '-C', str(repo), 'commit', '-m', 'some message'])

    result = invoke(['pull', 'test1', '--ask'], input='y\n')
    assert result.exit_code == 0
    assert result.stdout.startswith(
        '\nFollowing paths will most likely be replaced:',
    )
    assert '- ' in result.stdout
    assert ' (from "test1")' in result.stdout
    assert 'Proceed? [Y/n]: y' in result.stdout
    assert result.stdout.endswith('Operation successfully completed.\n')
    assert (source_dir / 'some_file').read_text() == 'some_content'

    # abort ask
    (repo / 'some_file').write_text('new_content')

    run_cmd(['git', '-C', str(repo), 'add', '.'])
    run_cmd(['git', '-C', str(repo), 'commit', '-m', 'some message'])

    result = invoke(['pull', 'test1', '--ask'], input='n\n')
    assert result.exit_code == 0
    assert (source_dir / 'some_file').read_text() == 'some_content'


def test_sync_with_verbose():
    repo = create_repo()
    some_file = create_file(name='some_file')

    config.save({
        'projects': {
            'test1': {
                'repository': str(repo),
                'branch': 'my_branch',
                'paths': {
                    'some_file': str(some_file),
                },
            },
        },
    })

    result = invoke(['push', 'test1', '--no-ask', '-v'])
    assert result.exit_code == 0
    assert '1 file changed, 0 insertions(+), 0 deletions(-)' in result.stdout
    assert 'Fetched ' in result.stdout
    assert 'Deleted ' in result.stdout
    assert (
        "branch 'my_branch' set up to track 'origin/my_branch'"
    ) in result.stdout
    assert 'Committed as "Auto push from' in result.stdout
    assert '[test1]"' in result.stdout

    result = invoke(['pull', 'test1', '--no-ask', '--verbose'])
    assert result.exit_code == 0
    assert 'my_branch  -> FETCH_HEAD' in result.stdout
    assert 'Put ' in result.stdout
    assert 'Deleted ' in result.stdout


def test_push_with_invalid_config():
    repo = create_repo()

    config.save({
        'projects': {
            'test1': {
                'repository': str(repo),
                'branch': 'my_branch',
                'paths': {
                    'some_file': 'invalid path ** / ^%$',
                },
            },
        },
    })

    result = invoke(['push', 'test1', '--no-ask'])
    assert result.exit_code == 201
    assert 'Error: "projects.test1.paths.some_file"' in result.stderr
    assert 'does not exist.\n' in result.stderr


def test_cannot_use_ref_with_multiple_projects():
    config.save({
        'projects': {
            'test1': {
                'branch': 'some',
                'repository': 'some',
                'paths': {},
            },
            'test2': {
                'branch': 'some',
                'repository': 'some',
                'paths': {},
            },
        },
    })

    result = invoke(['push', 'test1', 'test2', '--ref', 'someref'])
    assert result.exit_code == 206
    assert result.stderr == (
        'Error: --ref option cannot be used with multiple projects.\n'
    )

    result = invoke(['pull', 'test1', 'test2', '--ref', 'someref'])
    assert result.exit_code == 206
    assert result.stderr == (
        'Error: --ref option cannot be used with multiple projects.\n'
    )
