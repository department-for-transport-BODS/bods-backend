from enum import Enum
import time
from common_layer.db import BodsDB
from common_layer.logger import logger
from common_layer.exceptions.schema_exceptions import NoSchemaDefinition


class SchemaCategory(Enum):
    TXC   = "txc"
    NETEX = "netex"


def get_schema_definition_db_object(db: BodsDB, category: SchemaCategory):
    """Get TXC Schema record from the db given the category value

    Args:
        db: BODs DB instance
        category (SchemaCategory): value of the SchemaCategory for which record is required

    Returns:
        archive: database record for the object
    """
    if not db.session:
        raise ValueError("No database session provided")

    schema_definition = db.classes.pipelines_schemadefinition
    with db.session as session:
        start_query_op = time.time()
        schema_definition_obj = (
            session.query(schema_definition)
            .where(schema_definition.category == category.value)
            .first()
        )
        end_query_op = time.time()
        logger.info(f"Query execution time: {end_query_op-start_query_op:.2f} seconds")
        if schema_definition_obj is None:
            raise NoSchemaDefinition(category=category.value)
        return schema_definition_obj
