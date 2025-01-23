"""
PTI Pydantic Models
"""

import json
from pathlib import Path

from common_layer.database.models import DataQualityPTIObservation
from pydantic import BaseModel

from ..constants import NO_REF, REF_URL

GENERAL_REF = NO_REF + REF_URL


class Rule(BaseModel):
    """
    Observation Rules
    """

    test: str


class Observation(BaseModel):
    """
    PTI Observations
    """

    details: str
    category: str
    service_type: str
    reference: str
    context: str
    number: int
    rules: list[Rule]


class Header(BaseModel):
    """
    Header
    """

    namespaces: dict[str, str]
    version: str
    notes: str
    guidance_document: str


class Schema(BaseModel):
    """
    PTI Schema Loaded from Json
    """

    observations: list[Observation]
    header: Header

    @classmethod
    def from_path(cls, path: Path):
        """
        Loader for pti_schema.json
        """
        with path.open("r") as f:
            d = json.load(f)
            return cls(**d)


class PtiViolation(BaseModel):
    """
    PTI Violation Model
    """

    line: int
    filename: str
    name: str
    element_text: str | None = None
    observation: Observation

    @classmethod
    def make_observation(
        cls, revision_id: int, violation: "PtiViolation"
    ) -> DataQualityPTIObservation:
        """Creates a DataQualityPTIObservation from a violation instance."""
        return DataQualityPTIObservation(
            revision_id=revision_id,
            line=violation.line,
            filename=violation.filename,
            element=violation.name,
            details=violation.observation.details,
            category=violation.observation.category,
            reference=violation.observation.reference,
        )


class VehicleJourney(BaseModel):
    """
    Vehicle Journey Model
    """

    code: str
    line_ref: str
    journey_pattern_ref: str
    vehicle_journey_ref: str
    service_ref: str

    @classmethod
    def from_xml(cls, xml):
        """
        Vehicle Journey XML Parser
        """
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
    """
    Line Model
    """

    ref: str
    line_name: str

    @classmethod
    def from_xml(cls, xml):
        """
        Line XML Parser
        """
        namespaces = {"x": xml.nsmap.get(None)}
        ref = xml.xpath("string(@id)", namespaces=namespaces)
        line_name = xml.xpath("string(x:LineName)", namespaces=namespaces)
        return cls(ref=ref, line_name=line_name)
