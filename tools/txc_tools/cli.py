"""
TXC Reporting Tools with Typer Subcommands
"""

from pathlib import Path
from typing import Annotated

import typer

from .common import execute_process
from .models import AnalysisMode

app = typer.Typer()


@app.command(name="zip-size-report")
def zip_size_report(
    zip_files: Annotated[
        list[Path],
        typer.Argument(
            help="One or more zip files to process",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    sub_zip_workers: Annotated[
        int,
        typer.Option(
            "--sub-zip-workers",
            "-w",
            help="Number of worker threads for processing sub-zips",
            min=1,
            max=16,
            show_default=True,
        ),
    ] = 4,
) -> None:
    """
    Process multiple ZIP files in parallel, analyzing their XML contents and
    generating CSV reports.
    """
    execute_process(zip_files, AnalysisMode.SIZE, None, sub_zip_workers)


@app.command(name="zip-tag-counter")
def zip_tag_counter(
    zip_files: Annotated[
        list[Path],
        typer.Argument(
            help="One or more zip files to process",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    tag_name: Annotated[
        str,
        typer.Argument(help="XML tag name to search for"),
    ],
    sub_zip_workers: Annotated[
        int,
        typer.Option(
            "--sub-zip-workers",
            "-w",
            help="Number of worker threads for processing sub-zips",
            min=1,
            max=16,
            show_default=True,
        ),
    ] = 4,
) -> None:
    """
    Process multiple ZIP files in parallel, counting occurrences of specified
    XML tags and generating CSV reports.
    """
    execute_process(zip_files, AnalysisMode.TAG, tag_name, sub_zip_workers)


@app.command(name="zip-report-inventory")
def zip_txc_report(
    zip_files: Annotated[
        list[Path],
        typer.Argument(
            help="One or more zip files to process",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    sub_zip_workers: Annotated[
        int,
        typer.Option(
            "--sub-zip-workers",
            "-w",
            help="Number of worker threads for processing sub-zips",
            min=1,
            max=16,
            show_default=True,
        ),
    ] = 4,
) -> None:
    """
    Process multiple ZIP files in parallel, parsing TxC data from XML
    and generating CSV reports.
    """
    execute_process(zip_files, AnalysisMode.TXC, None, sub_zip_workers)


def cli() -> None:
    """
    Typer
    """
    app()


if __name__ == "__main__":
    cli()
