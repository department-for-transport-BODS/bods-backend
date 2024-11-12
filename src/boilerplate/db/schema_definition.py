import time
from common import LambdaEvent
from logger import logger
from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _
from bods_exception import NoSchemaDefinitionError


class SchemaCategory(TextChoices):
    TXC = ("txc", _("TxC"))
    NETEX = ("netex", _("NeTeX"))


def get_schema_definition_db_object(event: LambdaEvent, category: SchemaCategory):
    """Get TXC Schema record from the db given the category value

    Args:
        event (LambdaEvent): Event object which contains the db connection details
        category (SchemaCategory): value of the SchemaCategory for which record is required

    Returns:
        archive: database record for the object
    """
    if not event.db.session:
        raise ValueError("No database session provided")

    schema_definition = event.db.classes.pipelines_schemadefinition
    with event.db.session as session:
        start_query_op = time.time()
        schema_definition_obj = (
            session.query(schema_definition)
            .where(schema_definition.category == category)
            .first()
        )
        end_query_op = time.time()
        logger.info(f"Query execution time: {end_query_op-start_query_op:.2f} seconds")
        if schema_definition_obj is None:
            raise NoSchemaDefinitionError(category=category)
        return schema_definition_obj
