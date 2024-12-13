import logging
from pydantic import BaseModel
from os import environ
from sys import stdout

logger = logging.getLogger(__name__)
logger.setLevel(environ.get("LOG_LEVEL", "DEBUG"))
handler = logging.StreamHandler(stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class LoggerContext(BaseModel):
    component_name: str = ""
    class_name: str = ""
    object_id: int = -1


class DatasetPipelineLoggerContext(LoggerContext):
    class_name: str = "Dataset"
    component_name: str = "TimetablePipeline"
    revision_id: int = -1


class PipelineAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        if "context" in self.extra:
            context: LoggerContext = kwargs.pop("context", self.extra["context"])

            prefix = "[{component_name}] {class_name} {object_id} (Revision {revision_id}) => ".format(
                **context.model_dump()
            )
            msg = prefix + msg
        return msg, kwargs


def get_dataset_adapter_from_revision(revision_id: int, dataset_id: int) -> PipelineAdapter:
    context = DatasetPipelineLoggerContext(
        revision_id=revision_id, object_id=dataset_id
    )
    adapter: PipelineAdapter = PipelineAdapter(logger, {"context": context})
    return adapter
