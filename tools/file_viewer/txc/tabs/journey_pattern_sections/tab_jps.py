"""
Journey Pattern Sections
"""

from common_layer.xml.txc.models import (
    TXCData,
    TXCJourneyPatternSection,
    TXCJourneyPatternStopUsage,
    TXCJourneyPatternTimingLink,
    TXCRouteLink,
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

from ...utils_stoppoints import get_stop_point_details
from .tab_jps_tables import (
    from_stop_table,
    journey_pattern_timing_links_table,
    route_link_table,
    to_stop_table,
)


class JourneyPatternSectionsTab(Container):
    """
    TXC Journey Pattern Sections Info
    """

    selected_jps: Reactive[TXCJourneyPatternSection | None] = reactive(None)
    selected_jptl: Reactive[TXCJourneyPatternTimingLink | None] = reactive(None)

    def __init__(self, data: TXCData) -> None:
        super().__init__()
        self.data = data
        self.journey_pattern_sections_table = self.journey_pattern_sections_list()
        if self.data.JourneyPatternSections:
            self.selected_jps = self.data.JourneyPatternSections[0]
            if self.selected_jps.JourneyPatternTimingLink:
                self.selected_jptl = self.selected_jps.JourneyPatternTimingLink[0]

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                Static(
                    f"Journey Pattern Sections: {len(self.data.JourneyPatternSections)}"
                ),
                ScrollableContainer(self.journey_pattern_sections_table),
                Static("Timing Links"),
                Container(id="journey-pattern-timing-links-container"),
                id="journey-pattern-sections-container",
            ),
            Vertical(
                Static("From Stop"),
                Container(id="from-stop-container"),
                Static("To Stop"),
                Container(id="to-stop-container"),
                Static("Route Link"),
                Container(id="route-link-container"),
                id="journey-pattern-timing-link-details-container",
            ),
        )

    def journey_pattern_sections_list(self) -> DataTable[str]:
        """
        List of Journey Pattern Sections
        """
        table: DataTable[str] = DataTable(
            show_header=True,
            show_row_labels=True,
            zebra_stripes=True,
            header_height=1,
            show_cursor=True,
            cursor_type="row",
            name="Journey Pattern Sections",
            id="table-journey-pattern-sections",
        )
        table.styles.min_height = 20
        columns = ["ID", "Number of Timing Links", "Timing Link IDs"]
        table.add_columns(*columns)

        for section in self.data.JourneyPatternSections:
            table.add_row(
                section.id,
                str(len(section.JourneyPatternTimingLink)),
                ",".join([link.id for link in section.JourneyPatternTimingLink]),
            )

        return table

    def update_journey_pattern_timing_links_table(
        self, section: TXCJourneyPatternSection | None
    ) -> None:
        """
        Journey Pattern Timing Links Table Update
        """
        try:
            timing_links_container = self.query_one(
                "#journey-pattern-timing-links-container", Container
            )
        except NoMatches:
            return
        timing_links_container.remove_children()

        new_table = journey_pattern_timing_links_table()

        if section:
            for timing_link in section.JourneyPatternTimingLink:
                from_stop = get_stop_point_details(
                    self.data.StopPoints, timing_link.From.StopPointRef
                )
                to_stop = get_stop_point_details(
                    self.data.StopPoints, timing_link.To.StopPointRef
                )
                new_table.add_row(
                    timing_link.id,
                    from_stop.CommonName if from_stop else "",
                    to_stop.CommonName if to_stop else "",
                    timing_link.RouteLinkRef,
                    str(parse_duration(timing_link.RunTime)),
                    str(parse_duration(timing_link.From.WaitTime)),
                    timing_link.Distance if timing_link.Distance else "",
                    f"{timing_link.From.SequenceNumber} → {timing_link.To.SequenceNumber}",
                )

        timing_links_container.mount(ScrollableContainer(new_table))
        self.refresh()

    def update_from_stop_table(
        self, timing_link: TXCJourneyPatternTimingLink | None
    ) -> None:
        """
        From Stop Details Table Update
        """
        try:
            from_stop_container = self.query_one("#from-stop-container", Container)
        except NoMatches:
            return
        from_stop_container.remove_children()

        new_table = from_stop_table()

        if timing_link:
            from_stop: TXCJourneyPatternStopUsage = timing_link.From
            new_table.add_row(
                from_stop.StopPointRef,
                from_stop.WaitTime if from_stop.WaitTime else "",
                from_stop.Activity,
                from_stop.TimingStatus,
                from_stop.SequenceNumber if from_stop.SequenceNumber else "",
            )

        from_stop_container.mount(ScrollableContainer(new_table))
        self.refresh()

    def update_to_stop_table(
        self, timing_link: TXCJourneyPatternTimingLink | None
    ) -> None:
        """
        To Stop Details Table Update
        """
        try:
            to_stop_container = self.query_one("#to-stop-container", Container)
        except NoMatches:
            return
        to_stop_container.remove_children()

        new_table = to_stop_table()

        if timing_link:
            to_stop: TXCJourneyPatternStopUsage = timing_link.To
            new_table.add_row(
                to_stop.StopPointRef,
                str(parse_duration(to_stop.WaitTime)) if to_stop.WaitTime else "",
                to_stop.Activity,
                to_stop.TimingStatus,
                to_stop.SequenceNumber if to_stop.SequenceNumber else "",
            )

        to_stop_container.mount(ScrollableContainer(new_table))
        self.refresh()

    def update_route_link_table(
        self, timing_link: TXCJourneyPatternTimingLink | None
    ) -> None:
        """
        Route Link Details Table Update
        """
        try:
            route_link_container = self.query_one("#route-link-container", Container)
        except NoMatches:
            return
        route_link_container.remove_children()

        new_table = route_link_table()

        if timing_link:
            route_link_ref = timing_link.RouteLinkRef
            route_link: TXCRouteLink | None = None
            for section in self.data.RouteSections:
                route_link = next(
                    (link for link in section.RouteLink if link.id == route_link_ref),
                    None,
                )
                if route_link:
                    break

            if route_link:
                from_stop = get_stop_point_details(
                    self.data.StopPoints, route_link.From
                )
                to_stop = get_stop_point_details(self.data.StopPoints, route_link.To)
                new_table.add_row(
                    route_link.id,
                    from_stop.CommonName if from_stop else "",
                    to_stop.CommonName if to_stop else "",
                    str(route_link.Distance) if route_link.Distance else "",
                )

        route_link_container.mount(ScrollableContainer(new_table))
        self.refresh()

    @on(DataTable.RowSelected)
    def on_table_select(self, event: DataTable.RowSelected) -> None:
        """
        Handle selecting rows in tables
        """
        if event.data_table.id == "table-journey-pattern-sections":  # type: ignore
            data = event.data_table.get_row(event.row_key)  # type: ignore
            self.selected_jps = next(
                (
                    section
                    for section in self.data.JourneyPatternSections
                    if section.id == data[0]
                ),
                None,
            )
        elif event.data_table.id == "table-journey-pattern-timing-links":  # type: ignore
            data = event.data_table.get_row(event.row_key)  # type: ignore
            if self.selected_jps is not None:
                self.selected_jptl = next(
                    (
                        timing_link
                        for timing_link in self.selected_jps.JourneyPatternTimingLink
                        if timing_link.id == data[0]
                    ),
                    None,
                )

    # Watch Functions for Textual
    def watch_selected_jps(
        self,
        _old_section: TXCJourneyPatternSection | None,
        new_section: TXCJourneyPatternSection | None,
    ) -> None:
        """
        When the selected journey pattern section updates,
        Update the  to be the first timing link of the new section
        """
        self.update_journey_pattern_timing_links_table(new_section)

        #
        if new_section and new_section.JourneyPatternTimingLink:
            self.selected_jptl = new_section.JourneyPatternTimingLink[0]
        else:
            self.selected_jptl = None

    def watch_selected_jptl(
        self,
        _old_timing_link: TXCJourneyPatternTimingLink | None,
        new_timing_link: TXCJourneyPatternTimingLink | None,
    ) -> None:
        """
        When the selected journey pattern timing link updates,
          update the from/to stop and route link tables
        """
        self.update_from_stop_table(new_timing_link)
        self.update_to_stop_table(new_timing_link)
        self.update_route_link_table(new_timing_link)
