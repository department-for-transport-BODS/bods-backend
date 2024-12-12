import os
import sys
from contextlib import ExitStack
from typing import TextIO

from sqlalchemy.engine import create_engine
from sqlalchemy.schema import MetaData
from dotenv import load_dotenv

try:
    import citext
except ImportError:
    citext = None

try:
    import geoalchemy2
except ImportError:
    geoalchemy2 = None

try:
    import pgvector.sqlalchemy
except ImportError:
    pgvector = None

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points, version
else:
    from importlib.metadata import entry_points, version

load_dotenv()

# Tables to generate models for
MODEL_GEN_TABLES = [
    "avl_cavldataarchive",
    "data_quality_postschemaviolation",
    "data_quality_ptiobservation",
    "data_quality_ptivalidationresult",
    "data_quality_schemaviolation",
    "naptan_stoppoint",
    "organisation_dataset",
    "organisation_datasetrevision",
    "organisation_organisation",
    "organisation_txcfileattributes",
    "otc_localauthority",
    "otc_localauthority_registration_numbers",
    "otc_service",
    "pipelines_datasetetltaskresult",
    "pipelines_fileprocessingresult",
    "pipelines_pipelineerrorcode",
    "pipelines_pipelineprocessingstep",
    "pipelines_schemadefinition",
    "users_user",
]


def get_connection_string():
    db = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def sqlalchemy_model_generator() -> None:
    generators = {ep.name: ep for ep in entry_points(group="sqlacodegen.generators")}
    url = get_connection_string()
    options = ""
    schemas = "public"
    generator = "dataclasses"
    tables = MODEL_GEN_TABLES
    noviews = False
    outfile = "./src/boilerplate/common_layer/db/models.py"

    if not url:
        print("You must supply a url\n", file=sys.stderr)
        return

    if citext:
        print(f"Using sqlalchemy-citext {version('citext')}")

    if geoalchemy2:
        print(f"Using geoalchemy2 {version('geoalchemy2')}")

    if pgvector:
        print(f"Using pgvector {version('pgvector')}")

    # Use reflection to fill in the metadata
    engine = create_engine(url)
    metadata = MetaData()
    tables = [table.lower() for table in tables]
    schemas = schemas.split(",") if schemas else [None]
    options = set(options.split(",")) if options else set()

    for schema in schemas:
        metadata.reflect(engine, schema, not noviews, only=tables)

    # Instantiate the generator
    generator_class = generators[generator].load()
    generator = generator_class(metadata, engine, options)

    # Open the target file (if given)
    with ExitStack() as stack:
        outfile: TextIO
        if outfile:
            outfile = open(outfile, "w", encoding="utf-8")
            stack.enter_context(outfile)
        else:
            outfile = sys.stdout

        # Write the generated model code to the specified file or standard output
        print(f"Generating models for tables: {tables}")
        outfile.write(generator.generate())


sqlalchemy_model_generator()
