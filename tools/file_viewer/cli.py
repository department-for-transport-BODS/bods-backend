"""
File Viewer Cli
"""

from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from common_layer.xml.txc.parser.parser_txc import parse_txc_file
from structlog.stdlib import get_logger

from .txc.app_txc import TXCDataApp

log = get_logger()


class InputFormat(str, Enum):
    """
    Input Type
    """

    TXC = "txc"


cli = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)


@cli.command(name="file-viewer")
def file_viewer(
    input_file: Annotated[
        Path,
        typer.Argument(
            help="Specify a file or gtfs path to display information on",
        ),
    ],
    file_type: Annotated[
        InputFormat,
        typer.Option("--type", help="The File type"),
    ] = InputFormat.TXC,
):
    """
    View File information in a Command Line User Interface
    """
    log.info("data", input_file=input_file, file_type=file_type)

    if file_type == InputFormat.TXC:
        txc_data = parse_txc_file(input_file)
        TXCDataApp(txc_data).run()
    else:
        log.info("Unknown Input Format")


def run_cli():
    """
    Run the CLI
    """

    typer.run(file_viewer)
