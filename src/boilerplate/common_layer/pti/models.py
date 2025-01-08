import json
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel

from .constants import NO_REF, REF_PREFIX, REF_SUFFIX, REF_URL

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


class Header(BaseModel):
    namespaces: Dict[str, str]
    version: str
    notes: str
    guidance_document: str


class Schema(BaseModel):
    observations: List[Observation]
    header: Header

    @classmethod
    def from_path(cls, path: Path):
        with path.open("r") as f:
            d = json.load(f)
            return cls(**d)


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
            "observation_details": self.observation.details.format(
                element_text=self.element_text
            ),
            "reference": ref,
        }


class VehicleJourney(BaseModel):
    code: str
    line_ref: str
    journey_pattern_ref: str
    vehicle_journey_ref: str
    service_ref: str

    @classmethod
    def from_xml(cls, xml):
        namespaces = {"x": xml.nsmap.get(None)}
        code = xml.xpath("string(x:VehicleJourneyCode)", namespaces=namespaces)
        line_ref = xml.xpath("string(x:LineRef)", namespaces=namespaces)
        journey_pattern_ref = xml.xpath(
            "string(x:JourneyPatternRef)", namespaces=namespaces
        )
        vehicle_journey_ref = xml.xpath(
            "string(x:VehicleJourneyRef)", namespaces=namespaces
        )
        service_ref = xml.xpath("string(x:ServiceRef)", namespaces=namespaces)
        return cls(
            code=code,
            line_ref=line_ref,
            journey_pattern_ref=journey_pattern_ref,
            vehicle_journey_ref=vehicle_journey_ref,
            service_ref=service_ref,
        )


class Line(BaseModel):
    ref: str
    line_name: str

    @classmethod
    def from_xml(cls, xml):
        namespaces = {"x": xml.nsmap.get(None)}
        ref = xml.xpath("string(@id)", namespaces=namespaces)
        line_name = xml.xpath("string(x:LineName)", namespaces=namespaces)
        return cls(ref=ref, line_name=line_name)
