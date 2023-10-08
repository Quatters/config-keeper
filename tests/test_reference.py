from pathlib import Path

from tests.helpers import run_cmd


def test_reference_actuality():
    filename = 'REFERENCE.md'
    path = Path(__file__).parent.parent / filename
    assert path.is_file(), f'{filename} is not presented.'

    file_reference = path.read_text()

    result = run_cmd([
        'poetry', 'run', 'typer', 'config_keeper.commands', 'utils', 'docs',
        '--name', 'config-keeper',
    ])
    actual_reference = result.stdout

    msg = (
        'Use\n'
        '> poetry run typer config_keeper.commands utils docs --output '
        'REFERENCE.md --name config-keeper\n'
        'to update reference.\n'
    )
    assert file_reference.strip() == actual_reference.strip(), msg
