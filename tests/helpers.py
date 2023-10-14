import functools
import subprocess
import tempfile
import typing as t
from pathlib import Path

from config_keeper.commands import cli
from typer.testing import CliRunner

TMP_DIR = (Path(tempfile.gettempdir()) / 'config_keeper_tests').resolve()

cli_runner = CliRunner(mix_stderr=False)

invoke = functools.partial(cli_runner.invoke, cli)


def id_generator() -> t.Callable[[], int]:
    counter = 0
    def get_id() -> int:
        nonlocal counter
        counter += 1
        return counter
    return get_id


get_repo_id = id_generator()
get_dir_id = id_generator()
get_file_id = id_generator()


def create_repo(bare: bool = False) -> Path:
    """
    Creates empty repository and returns its path.
    """
    repo_dir = TMP_DIR / f'repo_{get_repo_id()}'
    cmd = ['git', 'init', str(repo_dir)]
    if bare:
        cmd.append('--bare')
    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        check=True,
    )
    return repo_dir


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
    )


def create_dir(*, parent: Path | None = None, name: str | None = None) -> Path:
    """
    Creates empty directory and returns its path. If parent not specified,
    directory will be placed at ./tests/__tmp__/.
    """
    dirname = name or f'dir_{get_dir_id()}'
    if parent is None:
        parent = TMP_DIR
    else:
        assert parent.is_dir(), 'parent must be a directory'
    dirpath = Path(parent) / dirname
    dirpath.mkdir()
    return dirpath


def create_file(
    *,
    parent: Path | None = None,
    content: str = '',
    name: str | None = None,
) -> Path:
    """
    Creates file with provided content and returns its path. If parent
    not specified, file will be placed at ./tests/__tmp__/.
    """
    filename = name or f'file_{get_file_id()}'
    if parent is None:
        parent = TMP_DIR
    else:
        assert parent.is_dir(), 'parent must be a directory'
    filepath = Path(parent) / filename
    filepath.write_text(content)
    return filepath
