"""
Zip Tools
"""

import typer
from structlog import get_logger

from .multi_zip_maker import multi_zip
from .xml_formatter import reformat
from .zip_repackage import repackage

log = get_logger()

app = typer.Typer(
    name="zip-tools", help="Tools for processing XML files in zip archives"
)

app.command()(repackage)
app.command()(reformat)
app.command()(multi_zip)

if __name__ == "__main__":
    app()
