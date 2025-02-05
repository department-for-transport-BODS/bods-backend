"""
TXC Reporting Tools with Typer Subcommands
"""

from pathlib import Path
from typing import Annotated, Optional

import typer

from .models import AnalysisMode, XmlTagLookUpInfo
from .parallel_processor import execute_process

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
    execute_process(
        zip_files=zip_files,
        mode=AnalysisMode.SIZE,
        sub_zip_workers=sub_zip_workers,
        lookup_info=XmlTagLookUpInfo(),
    )


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
    zip_structure: Annotated[
        str,
        typer.Argument(help="Zip file structure(flat or nested)"),
    ] = "flat",
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
    lookup_info = XmlTagLookUpInfo(tag_name=tag_name)
    execute_process(
        zip_files=zip_files,
        mode=AnalysisMode.TAG,
        sub_zip_workers=sub_zip_workers,
        lookup_info=lookup_info,
        zip_file_structure=zip_structure,
    )


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
    execute_process(
        zip_files=zip_files,
        mode=AnalysisMode.TXC,
        sub_zip_workers=sub_zip_workers,
        lookup_info=XmlTagLookUpInfo(),
    )


@app.command(name="zip-tag-search")
def zip_tag_with_parent(  # pylint: disable=too-many-arguments, too-many-positional-arguments
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
    search_path: Annotated[
        str,
        typer.Argument(help="XML parent path to search for"),
    ],
    id_elements: Annotated[
        Optional[str],
        typer.Argument(
            help='Identifier of tag(comma separated values eg. "id,ref,name"'
        ),
    ] = None,
    zip_structure: Annotated[
        str,
        typer.Argument(help="Zip file structure(flat or nested)"),
    ] = "flat",
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
    Process multiple ZIP files in parallel, searching tag in XML with respect to
    the path and generating CSV reports.
    """
    if id_elements is None:
        id_elements = "id,ref,name"

    id_elements_list = [it.strip() for it in id_elements.split(",")]
    lookup_info = XmlTagLookUpInfo(
        tag_name=tag_name, search_path=search_path, id_elements=id_elements_list
    )
    execute_process(
        zip_files=zip_files,
        mode=AnalysisMode.SEARCH,
        sub_zip_workers=sub_zip_workers,
        lookup_info=lookup_info,
        zip_file_structure=zip_structure,
    )


def cli() -> None:
    """
    Typer
    """
    app()


if __name__ == "__main__":
    cli()
