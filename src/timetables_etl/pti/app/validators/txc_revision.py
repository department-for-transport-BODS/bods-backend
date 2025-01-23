"""
PTI TXC Revision Validator
"""

from common_layer.dynamodb.models import TXCFileAttributes

from ..models.models_pti import Observation, PtiViolation

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
    """
    Validates revision numbers in TransXChange (TXC) files against existing revisions.

    Ensures that when a TXC file is updated:
    - Files with different modification dates have incrementing revision numbers
    - Files with the same modification date maintain consistent revision numbers

    The validator compares draft TXC files against live files that share the same
    service code and line names to enforce versioning.
    """

    def __init__(
        self,
        txc_file_attributes: TXCFileAttributes,
        live_txc_file_attributes: list[TXCFileAttributes],
    ):

        self._txc_file_attributes = txc_file_attributes
        self._live_attributes = live_txc_file_attributes
        self.violations: list[PtiViolation] = []

    def get_live_attributes_by_service_code_and_lines(
        self, code: str, lines: list[str]
    ) -> list[TXCFileAttributes]:
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
                        PtiViolation(
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
                    PtiViolation(
                        line=2,
                        filename=self._txc_file_attributes.filename,
                        name="RevisionNumber",
                        observation=REVISION_NUMBER_OBSERVATION,
                    )
                )
                break

    def get_violations(self) -> list[PtiViolation]:
        """
        Returns any revision violations.
        """
        if len(self._live_attributes) == 0:
            return self.violations

        self.validate_revision_number()
        return self.violations
