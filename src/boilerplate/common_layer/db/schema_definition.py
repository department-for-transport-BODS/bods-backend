import time
from common_layer.db.bods_db import BodsDB
from common_layer.logger import logger
from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _
from common_layer.exceptions.schema_exceptions import NoSchemaDefinition


class SchemaCategory(TextChoices):
    TXC = ("txc", _("TxC"))
    NETEX = ("netex", _("NeTeX"))


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
            .where(schema_definition.category == category)
            .first()
        )
        end_query_op = time.time()
        logger.info(f"Query execution time: {end_query_op-start_query_op:.2f} seconds")
        if schema_definition_obj is None:
            raise NoSchemaDefinition(category=category)
        return schema_definition_obj
