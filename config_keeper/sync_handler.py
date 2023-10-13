import datetime
import shutil
import subprocess
import tempfile
from pathlib import Path

from config_keeper import config
from config_keeper import exceptions as exc


def delete_dir(directory: str | Path):
    """
    Deletes the whole directory if it exists.
    """
    assert Path(directory).is_dir()
    shutil.rmtree(str(directory), ignore_errors=True)


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    executable = shutil.which(cmd[0])
    if not executable:
        raise exc.ExecutableNotFoundError(cmd[0])
    cmd = [executable] + cmd[1:]
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def clear_working_tree(path: Path | str):
    """
    Removes all files and directories in specified path except .git directory.
    """
    for entity in Path(path).iterdir():
        if entity.stem == '.git':
            continue
        if entity.is_dir():
            shutil.rmtree(entity)
        elif entity.is_file():
            entity.unlink()


def remote_branch_exists(
    repo: Path | str,
    branch: str,
    remote_name: str = 'origin',
) -> bool:
    full_name = f'refs/heads/{branch}'
    result = run_cmd([
        'git', '-C', str(repo), 'ls-remote', '--heads', remote_name,
        full_name,
    ])
    return full_name in result.stdout


class SyncHandler:
    def __init__(self, project: str, conf: config.TConfig):
        self.project = project
        self.conf = conf

    def push(self):
        branch = self.conf['projects'][self.project]['branch']
        repository = self.conf['projects'][self.project]['repository']

        temp_dir = tempfile.mkdtemp()

        run_cmd(['git', 'init', temp_dir])
        run_cmd(['git', '-C', temp_dir, 'remote', 'add', 'origin', repository])

        if remote_branch_exists(temp_dir, branch):
            run_cmd(['git', '-C', temp_dir, 'fetch', 'origin'])
            run_cmd(['git', '-C', temp_dir, 'checkout', branch])
            clear_working_tree(temp_dir)
        else:
            run_cmd(['git', '-C', temp_dir, 'checkout', '-b', branch])

        self._fetch_files(temp_dir)

        run_cmd(['git', '-C', temp_dir, 'add', '.'])
        run_cmd([
            'git', '-C', temp_dir, 'commit', '-m', self._get_commit_message(),
        ])
        run_cmd([
            'git', '-C', temp_dir, 'push', '--set-upstream', 'origin', branch,
        ])

        delete_dir(temp_dir)

    def pull(self):
        pull_dir = tempfile.mkdtemp()
        branch = self.conf['projects'][self.project]['branch']
        repository = self.conf['projects'][self.project]['repository']

        run_cmd(['git', 'init', pull_dir])
        run_cmd([
            'git', '-C', pull_dir, 'pull', repository, branch,
        ])

        self._put_in_places(pull_dir)
        delete_dir(pull_dir)

    def _fetch_files(self, directory: Path | str):
        directory = Path(directory)

        paths = self.conf['projects'][self.project]['paths']
        for path_name, str_path in paths.items():
            path = Path(str_path).expanduser().resolve()
            dest = str(directory / path_name)
            copy_args = (str_path, dest)
            if path.is_file():
                shutil.copy2(*copy_args)
            else:
                shutil.copytree(*copy_args)

    def _put_in_places(self, directory: Path | str):
        directory = Path(directory)
        paths = self.conf['projects'][self.project]['paths']

        for path_name, str_path in paths.items():
            source = directory / path_name
            dest = Path(str_path).expanduser().resolve()
            copy_args = (str(source), str_path)
            if source.exists():
                if dest.is_file():
                    dest.unlink()
                elif dest.is_dir():
                    shutil.rmtree(str(dest))

                if source.is_file():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(*copy_args)
                else:
                    shutil.copytree(*copy_args)

    def _get_commit_message(self) -> str:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        return f'Auto push from {now} [{self.project}]'
