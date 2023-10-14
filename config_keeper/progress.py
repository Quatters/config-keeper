from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from config_keeper.output import DefaultHighlighter


def spinner() -> Progress:
    return Progress(
        SpinnerColumn('dots', style='bold yellow'),
        TimeElapsedColumn(),
        TextColumn('{task.description}', highlighter=DefaultHighlighter()),
        transient=True,
    )
