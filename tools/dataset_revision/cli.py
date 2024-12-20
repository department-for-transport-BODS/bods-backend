"""
Creates Dataset Revisions in the database
"""

from datetime import UTC, datetime

import typer
from common_layer.database.client import SqlDB
from common_layer.database.models import OrganisationDatasetRevision
from common_layer.database.repos.repo_organisation import (
    OrganisationDatasetRevisionRepo,
)
from common_layer.json_logging import configure_logging
from structlog.stdlib import get_logger

from tests.factories.database.organisation import OrganisationDatasetRevisionFactory
from tools.common.db_tools import setup_process_db
from tools.common.models import TestConfig

app = typer.Typer()
log = get_logger()


def create_revision(
    dataset_id: int,
    filename: str,
    name: str,
    description: str,
    short_description: str,
    comment: str,
    db: SqlDB,
    is_published: bool = False,
    user_id: int | None = None,
) -> OrganisationDatasetRevision:
    """
    Create a new dataset revision
    """
    revision_data = OrganisationDatasetRevisionFactory(
        dataset_id=dataset_id,
        upload_file=filename,
        name=name,
        description=description,
        short_description=short_description,
        comment=comment,
        is_published=is_published,
        last_modified_user_id=user_id,
        published_by_id=user_id if is_published else None,
        published_at=datetime.now(UTC) if is_published else None,
    )

    repo = OrganisationDatasetRevisionRepo(db)
    revision = repo.insert(revision_data)
    log.info(
        "Created dataset revision",
        revision_id=revision.id,
        dataset_id=dataset_id,
        name=name,
    )
    return revision


@app.command()
def main(
    name: str = typer.Option(
        ...,
        "--name",
        help="Name of the revision",
    ),
    filename: str = typer.Option(
        "TXC.xml",
        "--filename",
        help="The filename for upload_file",
    ),
    dataset_id: int = typer.Option(
        123,
        "--dataset-id",
        help="The Dataset ID to create revision for",
    ),
    description: str = typer.Option(
        "Test Revision Created by CLI",
        "--description",
        help="Description of the revision",
    ),
    short_description: str = typer.Option(
        "Lambda ETL Test CLI",
        "--short-description",
        help="Short description (max 30 chars)",
    ),
    comment: str = typer.Option(
        "Test Comment",
        "--comment",
        help="Comment about the revision",
    ),
    user_id: int = typer.Option(
        None,
        "--user-id",
        help="User ID creating the revision",
    ),
    is_published: bool = typer.Option(
        False,
        "--publish",
        help="Whether to publish the revision immediately",
    ),
    db_host: str = typer.Option(
        "localhost",
        "--db-host",
        help="Database host",
    ),
    db_name: str = typer.Option(
        "bods-local",
        "--db-name",
        help="Database name",
    ),
    db_user: str = typer.Option(
        "bods-local",
        "--db-user",
        help="Database user",
    ),
    db_password: str = typer.Option(
        "bods-local",
        "--db-password",
        help="Database password",
    ),
    db_port: int = typer.Option(
        5432,
        "--db-port",
        help="Database port",
    ),
    log_json: bool = typer.Option(
        False,
        "--log-json",
        help="Enable Structured logging output",
    ),
):
    """Create a new dataset revision in the database"""
    if log_json:

        configure_logging()

    config = TestConfig(
        txc_paths=[],
        db_host=db_host,
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        db_port=db_port,
    )

    db = setup_process_db(config)

    try:
        revision = create_revision(
            dataset_id=dataset_id,
            name=name,
            filename=filename,
            description=description,
            short_description=short_description,
            comment=comment,
            db=db,
            is_published=is_published,
            user_id=user_id,
        )
        log.info("Successfully created revision", revision_id=revision.id)

    except Exception as e:
        log.error("Failed to create revision", error=str(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
