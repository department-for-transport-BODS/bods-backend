from typing import List

from common_layer.database.models.model_organisation import (
    OrganisationTXCFileAttributes,
)
from common_layer.dynamodb.models import TXCFileAttributes
from common_layer.pti.models import Observation, Violation

REVISION_NUMBER_OBSERVATION = Observation(
    details=(
        "Mandatory element incorrect in 'RevisionNumber' field. The "
        "RevisionNumber value should be greater than the previous "
        "RevisionNumber for the dataset in BODS."
    ),
    category="Versioning",
    service_type="All",
    reference="2.3",
    context="@RevisionNumber",
    number=0,
    rules=[],
)


class TXCRevisionValidator:
    def __init__(
        self,
        txc_file_attributes: TXCFileAttributes,
        live_txc_file_attributes: list[TXCFileAttributes],
    ):
        self._txc_file_attributes = txc_file_attributes
        self._live_attributes = live_txc_file_attributes
        self.violations = []

    def get_live_attributes_by_service_code_and_lines(
        self, code, lines
    ) -> List[TXCFileAttributes]:
        """
        Returns TXCFileAttributes with source_code equal to code and lines_names equal
        to lines.

        List is sorted by lowest revision number to highest.
        """
        # "this is a temporary change" - 25/07/2022
        filtered: list[TXCFileAttributes] = []
        draft_lines = sorted(lines)

        for attrs in self._live_attributes:
            lines_attr = sorted(attrs.line_names)
            if attrs.service_code == code and lines_attr == draft_lines:
                filtered.append(attrs)

        filtered.sort(key=lambda a: a.revision_number)
        return filtered

    def validate_revision_number(self) -> None:
        """
        Validates that TXCFileAttributes revision_number increments between revisions if the
        modification_datetime has changed.

        If multiple files with the same ServiceCode appear in the zip
        then we use modification_datetime as the attribute to distinguish
        when we expect the revision_number to be bumped.
        """

        live_revision_attributes = self.get_live_attributes_by_service_code_and_lines(
            self._txc_file_attributes.service_code, self._txc_file_attributes.line_names
        )
        if len(live_revision_attributes) == 0:
            return

        for live_attributes in live_revision_attributes:
            if (
                live_attributes.modification_datetime
                == self._txc_file_attributes.modification_datetime
            ):
                if (
                    live_attributes.revision_number
                    != self._txc_file_attributes.revision_number
                ):
                    self.violations.append(
                        Violation(
                            line=2,
                            filename=self._txc_file_attributes.filename,
                            name="RevisionNumber",
                            observation=REVISION_NUMBER_OBSERVATION,
                        )
                    )
                break

            if (
                live_attributes.revision_number
                >= self._txc_file_attributes.revision_number
            ):
                self.violations.append(
                    Violation(
                        line=2,
                        filename=self._txc_file_attributes.filename,
                        name="RevisionNumber",
                        observation=REVISION_NUMBER_OBSERVATION,
                    )
                )
                break

    def get_violations(self) -> List[Violation]:
        """
        Returns any revision violations.
        """
        if len(self._live_attributes) == 0:
            return self.violations

        self.validate_revision_number()
        return self.violations
