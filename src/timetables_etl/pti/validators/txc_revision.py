from typing import List, Optional

from common_layer.db import BodsDB
from common_layer.db.models import OrganisationDatasetrevision, OrganisationTxcfileattributes
from common_layer.db.repositories.dataset import DatasetRepository
from common_layer.db.repositories.dataset_revision import DatasetRevisionRepository
from common_layer.db.repositories.txc_file_attributes import TxcFileAttributesRepository
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
        self, revision: OrganisationDatasetrevision, txc_file_attributes: OrganisationTxcfileattributes, db: BodsDB
    ):
        self.revision = revision
        self.txc_file_attributes = txc_file_attributes
        self.violations = []
        self.db = db

        self._live_revision = None
        self._live_attributes = None

    @property
    def live_revision(self) -> Optional[OrganisationDatasetrevision]:
        """
        Returns the live revision if found
        """
        if self._live_revision is not None:
            return self._live_revision

        try:
            dataset_repo = DatasetRepository(self.db)
            dataset = dataset_repo.get_by_id(self.revision.dataset_id)

            dataset_revision_repo = DatasetRevisionRepository(self.db)
            live_revision = dataset_revision_repo.get_by_id(dataset.live_revision_id)

            self._live_revision = live_revision
            return self._live_revision
        except Exception:
            return None

    @property
    def live_attributes(self) -> List[OrganisationTxcfileattributes]:
        """
        Returns all the TXCFileAttributes of the live revision of this Dataset.
        """
        if self._live_attributes is not None:
            return self._live_attributes

        repo = TxcFileAttributesRepository(self.db)
        self._live_attributes = repo.get_all(revision_id=self.live_revision.id)
        return self._live_attributes

    def get_live_attributes_by_service_code_and_lines(self, code, lines) -> List[OrganisationTxcfileattributes]:
        """
        Returns TXCFileAttributes with source_code equal to code and lines_names equal
        to lines.

        List is sorted by lowest revision number to highest.
        """
        # "this is a temporary change" - 25/07/2022
        filtered = []
        draft_lines = sorted(lines)

        for attrs in self.live_attributes:
            lines_attr = sorted(attrs.line_names)
            if attrs.service_code == code and lines_attr == draft_lines:
                filtered.append(attrs)

        filtered.sort(key=lambda a: a.revision_number)
        return filtered

    def validate_revision_number(self) -> None:
        """
        Validates that TxcFileAttributes revision_number increments between revisions if the
        modification_datetime has changed.

        If multiple files with the same ServiceCode appear in the zip
        then we use modification_datetime as the attribute to distinguish
        when we expect the revision_number to be bumped.
        """

        live_revision_attributes = self.get_live_attributes_by_service_code_and_lines(
            self.txc_file_attributes.service_code, self.txc_file_attributes.line_names
        )
        if len(live_revision_attributes) == 0:
            return

        for live_attributes in live_revision_attributes:
            if live_attributes.modification_datetime == self.txc_file_attributes.modification_datetime:
                if live_attributes.revision_number != self.txc_file_attributes.revision_number:
                    self.violations.append(
                        Violation(
                            line=2,
                            filename=self.txc_file_attributes.filename,
                            name="RevisionNumber",
                            observation=REVISION_NUMBER_OBSERVATION,
                        )
                    )
                break

            if live_attributes.revision_number >= self.txc_file_attributes.revision_number:
                self.violations.append(
                    Violation(
                        line=2,
                        filename=self.txc_file_attributes.filename,
                        name="RevisionNumber",
                        observation=REVISION_NUMBER_OBSERVATION,
                    )
                )
                break

    def get_violations(self) -> List[Violation]:
        """
        Returns any revision violations.
        """
        if self.live_revision is None:
            return self.violations

        if len(self.live_attributes) == 0:
            return self.violations

        self.validate_revision_number()
        return self.violations
