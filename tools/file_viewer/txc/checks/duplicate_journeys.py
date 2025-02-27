"""
Check for Duplicate Journeys
"""

from collections import defaultdict

from common_layer.xml.txc.models import (
    TXCData,
    TXCFlexibleVehicleJourney,
    TXCVehicleJourney,
)
from structlog.stdlib import get_logger
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.css.query import NoMatches
from textual.reactive import Reactive, reactive
from textual.widgets import DataTable, Static

from ...checks import CheckResult

log = get_logger()


class DuplicateJourneysCheckData(CheckResult):
    """
    Whether there are duplicate journeys
    """

    journey_details: dict[str, list[TXCVehicleJourney | TXCFlexibleVehicleJourney]]


def get_journey_key(journey: TXCVehicleJourney | TXCFlexibleVehicleJourney) -> tuple:
    """
    Create a unique key for each journey based on its identifying attributes.
    """
    if isinstance(journey, TXCVehicleJourney):
        return (
            journey.DepartureTime,
            journey.JourneyPatternRef,
            (
                journey.OperatingProfile.model_dump_json()
                if journey.OperatingProfile
                else "?"
            ),
        )
    else:
        return (None, None, None)


def check_duplicate_journeys(data: TXCData) -> DuplicateJourneysCheckData:
    """
    Check for duplicate journeys in the TXCData
    Return a DuplicateJourneysCheckData instance
    """
    journey_map: dict[tuple, list[TXCVehicleJourney | TXCFlexibleVehicleJourney]] = (
        defaultdict(list)
    )
    journey_details: dict[str, list[TXCVehicleJourney | TXCFlexibleVehicleJourney]] = {}

    for journey in data.VehicleJourneys:
        key = get_journey_key(journey)
        journey_map[key].append(journey)

    for journeys in journey_map.values():
        if len(journeys) > 1:
            # Create a sorted, comma-separated list of VehicleJourneyCodes
            journey_codes = sorted(
                journey.VehicleJourneyCode
                for journey in journeys
                if journey.VehicleJourneyCode
            )
            if journey_codes:
                combined_key = ", ".join(journey_codes)
                journey_details[combined_key] = journeys

    return DuplicateJourneysCheckData(
        result=not bool(journey_details),
        journey_details=journey_details,
    )


def journey_details_table() -> DataTable:
    """
    Journey Details table
    """
    table = DataTable(
        show_header=True,
        show_row_labels=True,
        zebra_stripes=True,
        header_height=1,
        show_cursor=True,
        cursor_type="row",
        name="Journey Details",
        id="table-journey-details",
    )
    table.styles.min_height = 20
    columns = ["Matching Journey", "JourneyPattern", "Depature"]
    table.add_columns(*columns)
    return table


class DuplicateJourneysDetails(Container):
    """
    Duplicate Journeys Info
    """

    selected_journey_id: Reactive[str | None] = reactive(None)

    def __init__(self, data: DuplicateJourneysCheckData, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = data
        self.duplicate_journeys_table: DataTable = self.make_journeys_table()

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                Static(f"Duplicate Journeys: {len(self.data.journey_details.keys())}"),
                ScrollableContainer(self.duplicate_journeys_table),
                id="duplicate-journeys-container",
            ),
            Vertical(
                Static("Journey Details"),
                Container(id="journey-details-container"),
                id="journey-details-outer-container",
            ),
        )

    def make_journeys_table(self) -> DataTable:
        """
        Table of Duplicate Journeys
        """
        table = DataTable(
            show_header=True,
            show_row_labels=True,
            zebra_stripes=True,
            header_height=1,
            show_cursor=True,
            cursor_type="row",
            name="Duplicate Journeys",
            id="table-duplicate-journeys",
        )
        table.styles.min_height = 40
        columns = [
            "Vehicle Journeys",
            "Duplicates",
        ]
        table.add_columns(*columns)
        for journey in self.data.journey_details.keys():
            details = self.data.journey_details.get(journey, [])
            first_item = details[0] if details else None
            if first_item:
                table.add_row(
                    journey,
                    len(details),
                )
            else:
                table.add_row(journey, len(details), "", "")
        return table

    def update_journey_details_table(self, journey_id: str | None) -> None:
        """
        Journey Details Table Update
        """
        try:
            journey_details_container = self.query_one(
                "#journey-details-container", Container
            )
        except NoMatches:
            return
        journey_details_container.remove_children()

        new_table = journey_details_table()

        if journey_id and journey_id in self.data.journey_details:
            for journey in self.data.journey_details[journey_id]:
                new_table.add_row(
                    str(journey.VehicleJourneyCode),
                    journey.JourneyPatternRef,
                    (
                        journey.DepartureTime
                        if isinstance(journey, TXCVehicleJourney)
                        else None
                    ),
                )

        journey_details_container.mount(ScrollableContainer(new_table))
        self.refresh()

    @on(DataTable.RowSelected)
    def on_table_select(self, event: DataTable.RowSelected) -> None:
        """
        Handle selecting rows in tables
        """
        if event.data_table.id == "table-duplicate-journeys":
            data = event.data_table.get_row(event.row_key)
            self.selected_journey_id = data[0]

    # Watch Functions for Textual
    def watch_selected_journey_id(
        self, _old_journey_id: str | None, new_journey_id: str | None
    ) -> None:
        """
        When the selected journey ID updates, update the journey details table
        """
        self.update_journey_details_table(new_journey_id)


def check_duplicate_journeys_details(data: DuplicateJourneysCheckData) -> Container:
    """
    Implement the logic to retrieve details for duplicate journeys
    Return a Container with the relevant information
    """

    return DuplicateJourneysDetails(data)
