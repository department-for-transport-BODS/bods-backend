from pydantic import BaseModel
from typing import List, Optional
from pti.constants import (
    NO_REF,
    REF_PREFIX,
    REF_SUFFIX,
    REF_URL,
)
from pti.utils import get_important_note

GENERAL_REF = NO_REF + REF_URL


class Rule(BaseModel):
    test: str


class Observation(BaseModel):
    details: str
    category: str
    service_type: str
    reference: str
    context: str
    number: int
    rules: List[Rule]


class Violation(BaseModel):
    line: int
    filename: str
    name: str
    element_text: Optional[str] = None
    observation: Observation

    def to_pandas_dict(self):
        if self.observation.reference != "0":
            ref = REF_PREFIX + self.observation.reference + REF_SUFFIX + REF_URL
        else:
            ref = GENERAL_REF

        return {
            "observation_number": self.observation.number,
            "filename": self.filename,
            "line": self.line,
            "name": self.name,
            "observation_category": self.observation.category,
            "observation_details": self.observation.details.format(element_text=self.element_text),
            "reference": ref,
            "note": get_important_note(),
        }
