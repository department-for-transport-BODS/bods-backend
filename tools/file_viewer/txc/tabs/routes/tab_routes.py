"""
View Routes
"""

from common_layer.xml.txc.models import TXCData, TXCRoute, TXCRouteSection
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.css.query import NoMatches
from textual.reactive import Reactive, reactive
from textual.widgets import DataTable, Static

from ...utils_stoppoints import get_stop_point_details
from .tab_routes_tables import route_links_table, route_sections_list


class RoutesTab(Container):
    """
    TXC Routes Info
    """

    selected_route: Reactive[TXCRoute | None] = reactive(None)
    selected_route_section: Reactive[TXCRouteSection | None] = reactive(None)

    def __init__(self, data: TXCData, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = data
        self.routes_table: DataTable = self.routes_list()
        if self.data.Routes:
            self.selected_route = self.data.Routes[0]
            if self.selected_route.RouteSectionRef:
                self.selected_route_section = self.selected_route.RouteSectionRef[0]

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                Static(f"Routes: {len(self.data.Routes)}"),
                ScrollableContainer(self.routes_table),
                Container(id="route-sections-container"),
                id="routes-container",
            ),
            Vertical(
                Static("Route Links"),
                Container(id="route-links-container"),
                id="route-links-outer-container",
            ),
        )

    def routes_list(self) -> DataTable:
        """
        List of Routes
        """
        table = DataTable(
            show_header=True,
            show_row_labels=True,
            zebra_stripes=True,
            header_height=1,
            show_cursor=True,
            cursor_type="row",
            name="Routes",
            id="table-routes",
        )
        table.styles.min_height = 20
        table.styles.max_width = "95%"
        columns = [
            "ID",
            "Private Code",
            "Description",
            "Revision Number",
        ]
        table.add_columns(*columns)

        for route in self.data.Routes:
            table.add_row(
                route.id,
                route.PrivateCode,
                route.Description,
                str(route.RevisionNumber),
            )

        return table

    def update_route_sections_table(self, route: TXCRoute | None) -> None:
        """
        Route Sections Table Update
        """
        try:
            route_sections_container = self.query_one(
                "#route-sections-container", Container
            )
        except NoMatches:
            return
        route_sections_container.remove_children()

        new_table = route_sections_list()

        if route:
            for route_section in route.RouteSectionRef:
                new_table.add_row(
                    route_section.id,
                    str(len(route_section.RouteLink)),
                )

        route_sections_container.mount(ScrollableContainer(new_table))
        self.refresh()

    def update_route_links_table(self, route_section: TXCRouteSection | None) -> None:
        """
        Route Links Table
        """
        try:
            route_links_container = self.query_one("#route-links-container", Container)
        except NoMatches:
            return
        route_links_container.remove_children()

        new_table = route_links_table()

        if route_section:
            for route_link in route_section.RouteLink:
                from_stop = get_stop_point_details(
                    self.data.StopPoints, route_link.From
                )
                to_stop = get_stop_point_details(self.data.StopPoints, route_link.To)
                new_table.add_row(
                    route_link.id,
                    route_link.From,
                    from_stop.CommonName if from_stop else "",
                    route_link.To,
                    to_stop.CommonName if to_stop else "",
                    str(route_link.Distance) if route_link.Distance else "",
                )

        route_links_container.mount(ScrollableContainer(new_table))
        self.refresh()

    @on(DataTable.RowSelected)
    def on_table_select(self, event: DataTable.RowSelected) -> None:
        """
        Handle selecting rows in tables
        """
        if event.data_table.id == "table-routes":
            data = event.data_table.get_row(event.row_key)
            self.selected_route = next(
                (route for route in self.data.Routes if route.id == data[0]),
                None,
            )
            print(self.selected_route)
        elif event.data_table.id == "table-route-sections":
            data = event.data_table.get_row(event.row_key)
            if self.selected_route is not None:
                self.selected_route_section = next(
                    (
                        route_section
                        for route_section in self.selected_route.RouteSectionRef
                        if route_section.id == data[0]
                    ),
                    None,
                )

    # Watch Functions for Textual
    def watch_selected_route(
        self, _old_route: TXCRoute | None, new_route: TXCRoute | None
    ) -> None:
        """
        When the selected route updates, update the other tables
        """
        self.update_route_sections_table(new_route)

        # Update the selected_route_section to be the first section of the new route
        if new_route and new_route.RouteSectionRef:
            self.selected_route_section = new_route.RouteSectionRef[0]
        else:
            self.selected_route_section = None

    def watch_selected_route_section(
        self, _old_section: TXCRouteSection | None, new_section: TXCRouteSection | None
    ) -> None:
        """
        When the selected route section updates, update the route links table
        """
        self.update_route_links_table(new_section)
