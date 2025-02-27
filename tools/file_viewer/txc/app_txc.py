"""
TXC File Info App
"""

from common_layer.xml.txc.models import TXCData
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.widgets import DataTable, Footer, Header, Static, TabbedContent, TabPane

from ..checks import ChecksTab
from .checks import CHECKS
from .tabs import JourneyPatternSectionsTab, RoutesTab, ServicesTab, VehicleJourneysTab
from .utils_stoppoints import get_all_stop_point_details


class TXCDataApp(App):
    """
    Display ATCO-Data
    """

    def __init__(self, data: TXCData, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data: TXCData = data

    def compose(self) -> ComposeResult:
        yield Header(
            name="ATCO-CIF Data",
            show_clock=True,
        )
        with TabbedContent(initial="summary"):

            with TabPane("Summary", id="summary"):
                yield Container(
                    Horizontal(
                        Vertical(
                            ScrollableContainer(self.get_summary_text()),
                            Static("Operators"),
                            ScrollableContainer(self.display_operator_details()),
                            Static("Services"),
                            ScrollableContainer(self.display_service_details()),
                        ),
                        Container(
                            Vertical(
                                ScrollableContainer(self.display_stop_point_details()),
                            ),
                            id="data-tables",
                            classes="data-tables",
                        ),
                    )
                )
            with TabPane("Services", id="services"):
                yield ServicesTab(self.data)
            with TabPane("Routes", id="routes"):
                yield RoutesTab(self.data)
            with TabPane("Journey Pattern Sections", id="jps"):
                yield JourneyPatternSectionsTab(self.data)
            with TabPane("Vehicle Journeys", id="vj"):
                yield VehicleJourneysTab(self.data)
            with TabPane("Checks", id="checks"):
                yield ChecksTab(CHECKS, self.data)
        yield Footer()

    def get_summary_text(self) -> Container:
        """
        Summarise the TransXChange data in two columns
        """
        left_column_text = (
            f"Stop Points: {len(self.data.StopPoints)}\n"
            f"Routes: {len(self.data.Routes)}\n"
            f"Route Sections: {len(self.data.RouteSections)}\n"
        )

        right_column_text = (
            f"Journey Pattern Sections: {len(self.data.JourneyPatternSections)}\n"
            f"Vehicle Journeys: {len(self.data.VehicleJourneys)}\n"
            f"Operators: {len(self.data.Operators)}\n"
            f"Services: {len(self.data.Services)}\n"
        )

        left_column = Static(left_column_text)
        right_column = Static(right_column_text)
        left_column.styles.width = "50%"
        right_column.styles.width = "50%"
        columns = Container(Horizontal(left_column, right_column))
        return columns

    def display_operator_details(self) -> DataTable:
        """
        Operator ATCO-CIF Data
        """
        table = DataTable(
            show_header=True,
            show_row_labels=True,
            zebra_stripes=True,
            header_height=1,
            show_cursor=True,
            name="Operator Details",
        )
        table.styles.min_height = "20"
        table.add_columns(
            "Operator Code",
            "Short Name",
            "Licence Number",
            "Name on Licence",
            "Trading Name",
            "Licence Classification",
            "Primary Mode",
        )

        for operator in self.data.Operators:
            row_data = [
                operator.NationalOperatorCode,
                operator.OperatorShortName,
                operator.LicenceNumber,
                operator.OperatorNameOnLicence,
                operator.TradingName,
                operator.LicenceClassification,
                operator.PrimaryMode,
            ]
            table.add_row(*row_data)

        return table

    def display_service_details(self) -> DataTable:
        """
        Display Service Details
        """
        table = DataTable(
            show_header=True,
            show_row_labels=True,
            zebra_stripes=True,
            header_height=1,
            show_cursor=True,
            name="Service",
        )
        table.styles.min_height = 20
        table.add_columns(
            "Routes",
            "Origin",
            "Destination",
            "Start Date",
            "End Date",
            "Service Code",
            "Private Code",
            "RegisteredOperatorRef",
            "Lines",
            "Journey Patterns",
            "Public Use",
        )

        for service in self.data.Services:
            routes = (
                ", ".join(service.Lines[i].LineName for i in range(len(service.Lines)))
                if service.Lines
                else service.Lines[0].LineName
            )
            row_data = [
                routes,
                service.StandardService.Origin if service.StandardService else None,
                (
                    service.StandardService.Destination
                    if service.StandardService
                    else None
                ),
                service.StartDate.strftime("%Y-%m-%d"),
                service.EndDate.strftime("%Y-%m-%d") if service.EndDate else "",
                service.ServiceCode,
                service.PrivateCode,
                service.RegisteredOperatorRef,
                len(service.Lines),
                (
                    len(service.StandardService.JourneyPattern)
                    if service.StandardService
                    else None
                ),
                "Yes" if service.PublicUse else "No",
            ]
            table.add_row(*row_data)

        return table

    def display_stop_point_details(self) -> DataTable:
        """
        Table of Stop Points from TransXChange Data
        """
        stop_point_table = DataTable(
            show_header=True,
            show_row_labels=True,
            zebra_stripes=True,
            header_height=1,
            show_cursor=True,
            cursor_type="row",
            name="Stop Point Details",
        )
        stop_point_table.styles.min_height = 100
        columns = [
            "Type",
            "Stop Point Ref",
            "Common Name",
            "Indicator",
            "Locality Name",
            "Locality Qualifier",
        ]
        stop_point_table.add_columns(*columns)

        all_stop_point_details = get_all_stop_point_details(self.data.StopPoints)
        for details in all_stop_point_details:
            stop_point_table.add_row(
                details.type,
                details.StopPointRef,
                details.CommonName,
                details.Indicator or "",
                details.LocalityName or "",
                details.LocalityQualifier or "",
            )

        return stop_point_table
