"""
Display Vehicle Journey Information
"""

from datetime import datetime, timedelta

from common_layer.xml.txc.models import (
    TXCData,
    TXCFlexibleVehicleJourney,
    TXCJourneyPattern,
    TXCJourneyPatternTimingLink,
    TXCRoute,
    TXCVehicleJourney,
    TXCVehicleJourneyTimingLink,
)
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.css.query import NoMatches
from textual.reactive import Reactive, reactive
from textual.widgets import DataTable, Static

from src.timetables_etl.etl.app.transform.service_pattern_stops_durations import (
    parse_duration,
)

from ...utils_stoppoints import StopPointDetails, get_stop_point_details
from .tab_vehicle_journeys_tables import (
    journey_pattern_sections_table,
    journey_pattern_table,
    journey_pattern_timing_link_detail_table,
    route_table,
    vehicle_journey_timing_links_table,
)


class VehicleJourneysTab(Container):
    """
    TXC Vehicle Journeys Info
    """

    selected_vehicle_journey: Reactive[
        TXCVehicleJourney | TXCFlexibleVehicleJourney | None
    ] = reactive(None)
    selected_vj_timing_link: Reactive[TXCVehicleJourneyTimingLink | None] = reactive(
        None
    )
    selected_journey_pattern: Reactive[TXCJourneyPattern | None] = reactive(None)
    selected_route: Reactive[TXCRoute | None] = reactive(None)

    def __init__(self, data: TXCData, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = data
        self.vehicle_journeys_table: DataTable = self.vehicle_journeys_list()
        if self.data.VehicleJourneys:
            self.selected_vehicle_journey = self.data.VehicleJourneys[0]
            if isinstance(self.selected_vehicle_journey, TXCVehicleJourney):
                if self.selected_vehicle_journey.VehicleJourneyTimingLink:
                    self.selected_vj_timing_link = (
                        self.selected_vehicle_journey.VehicleJourneyTimingLink[0]
                    )

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                Static(f"Vehicle Journeys: {len(self.data.VehicleJourneys)}"),
                ScrollableContainer(self.vehicle_journeys_table),
                Static("Vehicle Journey Timing Links"),
                Container(id="vehicle-journey-timing-links-container"),
                id="vehicle-journeys-container",
            ),
            Vertical(
                Static("Journey Pattern"),
                Container(id="journey-pattern-container"),
                Static("Journey Pattern Sections"),
                Container(id="journey-pattern-sections-container"),
                Static("Route"),
                Container(id="route-container"),
                Static("Selected JPTL Details"),
                Container(id="journey-pattern-timing-link-detail-container"),
                id="vehicle-journey-details-container",
            ),
        )

    def vehicle_journeys_list(self) -> DataTable:
        """
        List of Vehicle Journeys
        """
        table = DataTable(
            show_header=True,
            show_row_labels=True,
            zebra_stripes=True,
            header_height=1,
            show_cursor=True,
            cursor_type="row",
            name="Vehicle Journeys",
            id="table-vehicle-journeys",
        )
        table.styles.min_height = 20
        columns = [
            "VJ Code",
            "Journey Pattern Ref",
            "Departure Time",
            "Sequence Number",
            "Private Code",
            "Destination Display",
            "Operator Ref",
            "Service Ref",
            "Line Ref",
        ]
        table.add_columns(*columns)

        for journey in self.data.VehicleJourneys:
            table.add_row(
                journey.VehicleJourneyCode,
                journey.JourneyPatternRef if journey.JourneyPatternRef else "",
                journey.DepartureTime if isinstance(journey, TXCVehicleJourney) else "",
                journey.SequenceNumber if journey.SequenceNumber else "",
                journey.PrivateCode if journey.PrivateCode else "",
                journey.DestinationDisplay if journey.DestinationDisplay else "",
                journey.OperatorRef if journey.OperatorRef else "",
                journey.ServiceRef if journey.ServiceRef else "",
                journey.LineRef if journey.LineRef else "",
            )

        return table

    def update_vehicle_journey_timing_links_table(
        self, journey: TXCVehicleJourney | None
    ) -> None:
        """
        Vehicle Journey Timing Links Table Update
        """
        try:
            timing_links_container = self.query_one(
                "#vehicle-journey-timing-links-container", Container
            )
        except NoMatches:
            return
        timing_links_container.remove_children()

        new_table = vehicle_journey_timing_links_table()

        if journey and journey.VehicleJourneyTimingLink:
            start_time = datetime.strptime(journey.DepartureTime, "%H:%M:%S")
            current_time = start_time

            for timing_link in journey.VehicleJourneyTimingLink:
                wait_time = parse_duration(
                    timing_link.From.WaitTime
                    if timing_link.From and timing_link.From.WaitTime
                    else "PT0H0M0S"
                )
                run_time = (
                    parse_duration(timing_link.RunTime)
                    if timing_link.RunTime
                    else timedelta()
                )

                # Calculate departure time (current time + wait time)
                departure_time = current_time + wait_time

                # Calculate arrival time (departure time + run time)
                arrival_time = departure_time + run_time

                # Get sequence numbers from the corresponding JPTL if available
                sequence_text = ""
                if self.selected_journey_pattern:
                    # Find the matching JPTL
                    jptl_info = self.find_journey_pattern_timing_link(
                        timing_link.JourneyPatternTimingLinkRef
                    )
                    if jptl_info:
                        jptl, _, _ = jptl_info
                        from_seq = (
                            jptl.From.SequenceNumber
                            if jptl.From and hasattr(jptl.From, "SequenceNumber")
                            else ""
                        )
                        to_seq = (
                            jptl.To.SequenceNumber
                            if jptl.To and hasattr(jptl.To, "SequenceNumber")
                            else ""
                        )
                        if from_seq and to_seq:
                            sequence_text = f"{from_seq} → {to_seq}"

                new_table.add_row(
                    timing_link.id if timing_link.id else "",
                    timing_link.JourneyPatternTimingLinkRef,
                    (
                        timing_link.VehicleJourneyRef
                        if timing_link.VehicleJourneyRef
                        else ""
                    ),
                    str(run_time),
                    str(wait_time),
                    arrival_time.strftime("%H:%M:%S"),  # Arrival column
                    departure_time.strftime("%H:%M:%S"),  # Departure column
                    sequence_text,  # New sequence column
                )

                # Update current_time for the next iteration
                current_time = arrival_time

        timing_links_container.mount(ScrollableContainer(new_table))
        self.refresh()

    def update_journey_pattern_table(
        self, journey_pattern: TXCJourneyPattern | None
    ) -> None:
        """
        Journey Pattern Details Table Update
        """
        try:
            journey_pattern_container = self.query_one(
                "#journey-pattern-container", Container
            )
        except NoMatches:
            return
        journey_pattern_container.remove_children()

        new_table = journey_pattern_table()

        if journey_pattern:
            new_table.add_row(
                journey_pattern.id,
                journey_pattern.PrivateCode if journey_pattern.PrivateCode else "",
                journey_pattern.DestinationDisplay,
                journey_pattern.OperatorRef if journey_pattern.OperatorRef else "",
                journey_pattern.Direction,
                journey_pattern.RouteRef,
                journey_pattern.Description if journey_pattern.Description else "",
                journey_pattern.LayoverPoint if journey_pattern.LayoverPoint else "",
            )

        journey_pattern_container.mount(ScrollableContainer(new_table))
        self.refresh()

    def update_journey_pattern_sections_table(
        self, journey_pattern: TXCJourneyPattern | None
    ) -> None:
        """
        Journey Pattern Sections Table Update
        """
        try:
            journey_pattern_sections_container = self.query_one(
                "#journey-pattern-sections-container", Container
            )
        except NoMatches:
            return
        journey_pattern_sections_container.remove_children()

        new_table = journey_pattern_sections_table()

        if journey_pattern:
            for section_ref in journey_pattern.JourneyPatternSectionRefs:
                new_table.add_row(section_ref)

        journey_pattern_sections_container.mount(ScrollableContainer(new_table))
        self.refresh()

    def update_route_table(self, route: TXCRoute | None) -> None:
        """
        Route Details Table Update
        """
        try:
            route_container = self.query_one("#route-container", Container)
        except NoMatches:
            return
        route_container.remove_children()

        new_table = route_table()

        if route:
            new_table.add_row(
                route.id,
                route.PrivateCode if route.PrivateCode else "",
                route.Description if route.Description else "",
                str(route.RevisionNumber) if route.RevisionNumber else "",
            )

        route_container.mount(ScrollableContainer(new_table))
        self.refresh()

    @on(DataTable.RowSelected)
    def on_table_select(self, event: DataTable.RowSelected) -> None:
        """
        Handle selecting rows in tables
        """
        if event.data_table.id == "table-vehicle-journeys":
            data = event.data_table.get_row(event.row_key)
            self.selected_vehicle_journey = next(
                (
                    journey
                    for journey in self.data.VehicleJourneys
                    if journey.VehicleJourneyCode == data[0]
                ),
                None,
            )
        elif event.data_table.id == "table-vehicle-journey-timing-links":
            data = event.data_table.get_row(event.row_key)
            if self.selected_vehicle_journey is not None and isinstance(
                self.selected_vehicle_journey, TXCVehicleJourney
            ):
                self.selected_vj_timing_link = next(
                    (
                        timing_link
                        for timing_link in self.selected_vehicle_journey.VehicleJourneyTimingLink
                        if timing_link.id == data[0]
                    ),
                    None,
                )

    # Watch Functions for Textual
    def watch_selected_vehicle_journey(
        self,
        _old_journey: TXCVehicleJourney | None,
        new_journey: TXCVehicleJourney | None,
    ) -> None:
        """
        When the selected vehicle journey updates, update the timing links table and journey pattern
        """
        self.update_vehicle_journey_timing_links_table(new_journey)

        if new_journey and new_journey.JourneyPatternRef:
            service = next(
                (
                    service
                    for service in self.data.Services
                    if service.ServiceCode == new_journey.ServiceRef
                ),
                None,
            )
            if service and service.StandardService:
                self.selected_journey_pattern = next(
                    (
                        journey_pattern
                        for journey_pattern in service.StandardService.JourneyPattern
                        if journey_pattern.id == new_journey.JourneyPatternRef
                    ),
                    None,
                )
            else:
                self.selected_journey_pattern = None
        else:
            self.selected_journey_pattern = None

    def watch_selected_journey_pattern(
        self,
        _old_pattern: TXCJourneyPattern | None,
        new_pattern: TXCJourneyPattern | None,
    ) -> None:
        """
        When the selected journey pattern updates
        , update the journey pattern details and sections tables
        """
        self.update_journey_pattern_table(new_pattern)
        self.update_journey_pattern_sections_table(new_pattern)

        if new_pattern:
            self.selected_route = next(
                (
                    route
                    for route in self.data.Routes
                    if route.id == new_pattern.RouteRef
                ),
                None,
            )
        else:
            self.selected_route = None

    def watch_selected_route(
        self,
        _old_route: TXCRoute | None,
        new_route: TXCRoute | None,
    ) -> None:
        """
        When the selected route updates, update the route details table
        """
        self.update_route_table(new_route)

    def find_journey_pattern_timing_link(self, jptl_ref: str) -> (
        tuple[
            TXCJourneyPatternTimingLink,
            StopPointDetails | None,
            StopPointDetails | None,
        ]
        | None
    ):
        """
        Find a Journey Pattern Timing Link by its reference ID
        Returns the JPTL and from/to stop details as a tuple
        """
        if not self.selected_journey_pattern:
            return None

        # Get all Journey Pattern Sections referenced by this Journey Pattern
        for section_ref in self.selected_journey_pattern.JourneyPatternSectionRefs:
            # Find the actual section object
            section = next(
                (
                    section
                    for section in self.data.JourneyPatternSections
                    if section.id == section_ref
                ),
                None,
            )

            if section:
                # Look for the timing link with matching ID
                jptl = next(
                    (
                        link
                        for link in section.JourneyPatternTimingLink
                        if link.id == jptl_ref
                    ),
                    None,
                )

                if jptl:
                    # Get stop details
                    from_stop = (
                        get_stop_point_details(
                            self.data.StopPoints, jptl.From.StopPointRef
                        )
                        if jptl.From
                        else None
                    )

                    to_stop = (
                        get_stop_point_details(
                            self.data.StopPoints, jptl.To.StopPointRef
                        )
                        if jptl.To
                        else None
                    )

                    return (jptl, from_stop, to_stop)

        return None

    def update_journey_pattern_timing_link_detail(
        self, vjtl: TXCVehicleJourneyTimingLink | None
    ) -> None:
        """
        Update the Journey Pattern Timing Link details table
        based on the selected Vehicle Journey Timing Link
        """
        try:
            jptl_detail_container = self.query_one(
                "#journey-pattern-timing-link-detail-container", Container
            )
        except NoMatches:
            return

        jptl_detail_container.remove_children()
        new_table = journey_pattern_timing_link_detail_table()

        if vjtl and vjtl.JourneyPatternTimingLinkRef:
            jptl_info = self.find_journey_pattern_timing_link(
                vjtl.JourneyPatternTimingLinkRef
            )

            if jptl_info:
                jptl, from_stop, to_stop = jptl_info

                new_table.add_row(
                    jptl.id,
                    from_stop.CommonName if from_stop else "",
                    to_stop.CommonName if to_stop else "",
                    jptl.RouteLinkRef if hasattr(jptl, "RouteLinkRef") else "",
                    parse_duration(jptl.RunTime) if jptl.RunTime else "",
                    (
                        parse_duration(jptl.From.WaitTime)
                        if jptl.From and jptl.From.WaitTime
                        else ""
                    ),
                    (
                        jptl.Distance
                        if hasattr(jptl, "Distance") and jptl.Distance
                        else ""
                    ),
                    from_stop.StopPointRef if from_stop else "",
                    to_stop.StopPointRef if to_stop else "",
                )

        jptl_detail_container.mount(ScrollableContainer(new_table))
        self.refresh()

    def watch_selected_vj_timing_link(
        self,
        _old_timing_link: TXCVehicleJourneyTimingLink | None,
        new_timing_link: TXCVehicleJourneyTimingLink | None,
    ) -> None:
        """
        When the selected vehicle journey timing link updates, update the JPTL details
        """
        self.update_journey_pattern_timing_link_detail(new_timing_link)
