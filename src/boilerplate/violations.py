from pydantic import BaseModel
from pathlib import Path


class BaseSchemaViolation(BaseModel):
    filename: str
    line: int
    details: str
    revision_id: int

    @classmethod
    def from_error(cls, error, revision_id):
        filename = Path(error.filename).name
        return cls(
            filename=filename,
            line=error.line,
            details=error.message,
            revision_id=revision_id,
        )
