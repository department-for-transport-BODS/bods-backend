"""
XML Tools
"""

from pathlib import Path

import typer
from structlog.stdlib import get_logger

log = get_logger()


def get_xml_paths(paths: list[Path]) -> list[Path]:
    """
    For a list of paths (e.g. folders or XMLs), return a list of the paths to the XML files
    """
    xml_paths: list[Path] = []

    if not paths:
        log.info("No paths provided, returning []")
        return []
    for path in paths:
        if path.is_dir():
            xml_paths.extend(path.glob("**/*.xml"))
        elif path.is_file() and path.suffix.lower() == ".xml":
            xml_paths.append(path)
        else:
            log.warning("Skipping invalid path", path=path)

    if not xml_paths:
        log.error("No valid XML files found in the specified paths", paths=paths)
        raise typer.Exit(code=1)

    return xml_paths
