"""
Service Information
"""

from common_layer.xml.txc.models import TXCData, TXCService
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.reactive import Reactive, reactive
from textual.widgets import DataTable, Static


class ServicesTab(Container):
    """
    TXC Service Info
    """

    selected_service: Reactive[TXCService | None] = reactive(None)

    def __init__(self, data: TXCData, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = data
        self.selected_service = self.data.Services[0]

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                ScrollableContainer(self.services_list()),
                id="journey-data-table",
            ),
            Vertical(
                Container(
                    Static("Journey Patterns"),
                    ScrollableContainer(self.journey_patterns_table()),
                    Static("Lines"),
                    ScrollableContainer(self.lines_table()),
                    id="selected-service-details-container",
                ),
            ),
        )

    def services_list(self) -> DataTable:
        """
        List of Services
        Should be 1
        """
        service_table = DataTable(
            show_header=True,
            show_row_labels=True,
            zebra_stripes=True,
            header_height=1,
            show_cursor=True,
            cursor_type="row",
            name="Service Details",
            id="table-services",
        )
        service_table.styles.min_height = "20"
        service_table.styles.max_width = "95%"
        columns = [
            "Service Code",
            "Private Code",
            "Operator Ref",
            "Public Use",
            "Start Date",
            "End Date",
            "Origin",
            "Destination",
            "Journey Patterns",
            "Lines",
            "Mode",
        ]
        service_table.add_columns(*columns)

        for service in self.data.Services:
            service_code = service.ServiceCode
            private_code = service.PrivateCode
            registered_operator_ref = service.RegisteredOperatorRef
            public_use = "Yes" if service.PublicUse else "No"
            start_date = service.StartDate.strftime("%Y-%m-%d")
            end_date = service.EndDate.strftime("%Y-%m-%d") if service.EndDate else ""
            origin = service.StandardService.Origin if service.StandardService else ""
            destination = (
                service.StandardService.Destination if service.StandardService else ""
            )
            journey_patterns = (
                len(service.StandardService.JourneyPattern)
                if service.StandardService
                else ""
            )
            lines = len(service.Lines)
            mode = service.Mode

            service_table.add_row(
                service_code,
                private_code,
                registered_operator_ref,
                public_use,
                start_date,
                end_date,
                origin,
                destination,
                str(journey_patterns),
                str(lines),
                mode,
            )

        return service_table

    def journey_patterns_table(self) -> DataTable:
        """
        Table of Journey Patterns for the selected service
        """
        journey_patterns_table = DataTable(
            show_header=True,
            show_row_labels=True,
            zebra_stripes=True,
            header_height=1,
            show_cursor=True,
            cursor_type="row",
            name="Journey Patterns",
            id="table-journey-patterns",
        )
        columns = [
            "ID",
            "Private Code",
            "Destination Display",
            "Operator Ref",
            "Direction",
            "Route Ref",
            "Journey Pattern Section Refs",
            "Description",
            "Layover Point",
        ]
        journey_patterns_table.add_columns(*columns)

        if self.selected_service:
            if self.selected_service.StandardService:
                for (
                    journey_pattern
                ) in self.selected_service.StandardService.JourneyPattern:
                    journey_patterns_table.add_row(
                        journey_pattern.id,
                        journey_pattern.PrivateCode,
                        journey_pattern.DestinationDisplay,
                        journey_pattern.OperatorRef,
                        journey_pattern.Direction,
                        journey_pattern.RouteRef,
                        ", ".join(journey_pattern.JourneyPatternSectionRefs),
                        journey_pattern.Description,
                        journey_pattern.LayoverPoint,
                    )

        return journey_patterns_table

    def lines_table(self) -> DataTable:
        """
        Table of Lines for the selected service
        """
        lines_table = DataTable(
            show_header=True,
            show_row_labels=True,
            zebra_stripes=True,
            header_height=1,
            show_cursor=True,
            cursor_type="row",
            name="Lines",
            id="table-lines",
        )
        lines_table.styles.min_height = "50"
        columns = [
            "ID",
            "Line Name",
            "Marketing Name",
            "Outbound Origin",
            "Outbound Destination",
            "Outbound Description",
            "Inbound Origin",
            "Inbound Destination",
            "Inbound Description",
        ]
        lines_table.add_columns(*columns)

        if self.selected_service:
            for line in self.selected_service.Lines:
                outbound_origin = (
                    line.OutboundDescription.Origin if line.OutboundDescription else ""
                )
                outbound_destination = (
                    line.OutboundDescription.Destination
                    if line.OutboundDescription
                    else ""
                )
                outbound_description = (
                    line.OutboundDescription.Description
                    if line.OutboundDescription
                    else ""
                )
                inbound_origin = (
                    line.InboundDescription.Origin if line.InboundDescription else ""
                )
                inbound_destination = (
                    line.InboundDescription.Destination
                    if line.InboundDescription
                    else ""
                )
                inbound_description = (
                    line.InboundDescription.Description
                    if line.InboundDescription
                    else ""
                )

                lines_table.add_row(
                    line.id,
                    line.LineName,
                    line.MarketingName,
                    outbound_origin,
                    outbound_destination,
                    outbound_description,
                    inbound_origin,
                    inbound_destination,
                    inbound_description,
                )

        return lines_table

    @on(DataTable.RowSelected)
    def on_table_select(self, event: DataTable.RowSelected) -> None:
        """
        Handle Selecting buttons
        """
        if event.data_table.id == "table-services":
            data = event.data_table.get_row(event.row_key)
            self.selected_service = next(
                (
                    service
                    for service in self.data.Services
                    if service.ServiceCode == data[0]
                ),
                None,
            )
