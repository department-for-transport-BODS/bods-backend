"""
Pretty Console Output
"""

from rich import print as pprint
from rich.columns import Columns
from rich.panel import Panel
from rich.rule import Rule


def print_columns(title: str, data: list[str]):
    """
    Print columns in the terminal
    """
    rule = Rule(title=title)
    pprint(rule)
    columns = Columns(data, equal=True, expand=True)
    output = Panel(columns)
    pprint(output)
