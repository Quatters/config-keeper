from rich.columns import Columns
from rich.console import Console, RenderableType
from rich.highlighter import (
    ReprHighlighter,
    _combine_regex,  # pyright: ignore [reportPrivateUsage]
)
from rich.panel import Panel


class DefaultHighlighter(ReprHighlighter):
    highlights = [
        r'(?P<tag_start><)(?P<tag_name>[-\w.:|]*)(?P<tag_contents>[\w\W]*)(?P<tag_end>>)',
        r'(?P<attrib_name>[\w_]{1,50})=(?P<attrib_value>"?[\w_]+"?)?',
        r'(?P<brace>[][{}()])',
        _combine_regex(
            r'(?P<ipv4>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})',
            r'(?P<ipv6>([A-Fa-f0-9]{1,4}::?){1,7}[A-Fa-f0-9]{1,4})',
            r'(?P<eui64>(?:[0-9A-Fa-f]{1,2}-){7}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{1,2}:){7}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{4}\.){3}[0-9A-Fa-f]{4})',
            r'(?P<eui48>(?:[0-9A-Fa-f]{1,2}-){5}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{1,2}:){5}[0-9A-Fa-f]{1,2}|(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4})',
            r'(?P<uuid>[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})',
            r'(?P<call>[\w.]*?)\(',
            r'\b(?P<bool_true>True)\b|\b(?P<bool_false>False)\b|\b(?P<none>None)\b',
            r'(?P<number_complex>(?<!\w)(?:\-?[0-9]+\.?[0-9]*(?:e[-+]?\d+?)?)(?:[-+](?:[0-9]+\.?[0-9]*(?:e[-+]?\d+)?))?j)',
            r'(?P<number>(?<!\w)\-?[0-9]+\.?[0-9]*(e[-+]?\d+?)?\b|0x[0-9a-fA-F]*)',
            r'(?P<path>\B(/[-\w._+]+)*\/)(?P<filename>[-\w._+]*)?',
            r"(?<![\\\w])(?P<str>b?'''.*?(?<!\\)'''|b?'.*?(?<!\\)'|b?\"\"\".*?(?<!\\)\"\"\"|b?\".*?(?<!\\)\")",
            r'(?P<url>(file|https|http|ws|wss)://[-0-9a-zA-Z$_+!`(),.?/;:&=%#~]*)',
        ),
    ]


highlighter = DefaultHighlighter()
console = Console(highlighter=highlighter)
errconsole = Console(highlighter=highlighter, stderr=True)


def print_project_saved(project: str):
    console.print(f'Project "{project}" saved.')


def print_warning(msg: str):
    errconsole.print(f'[yellow]Warning:[/yellow] {msg}')


def print_error(msg: str):
    errconsole.print(f'[red]Error:[/red] {msg}')


def print_critical(msg: str):
    errconsole.print(f'[violet]Critical:[/violet] {msg}')


def print_tip(msg: str):
    console.print(f'[yellow]Tip:[/yellow] {msg}')


def format_panel_columns(d: dict[str, str]) -> RenderableType:
    columns: list[RenderableType] = []
    for key, output in d.items():
        columns.append(Panel(
            output,
            title=key,
            title_align='left',
            highlight=True,
        ))
    return Columns(columns, expand=True)
