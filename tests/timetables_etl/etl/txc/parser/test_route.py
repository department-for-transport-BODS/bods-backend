"""
Testing Route XML Parsing
"""

import pytest
from lxml import etree

from timetables_etl.etl.app.txc.models import TXCRoute, TXCRouteLink, TXCRouteSection
from timetables_etl.etl.app.txc.parser.routes import parse_routes


@pytest.mark.parametrize(
    "xml_string, route_sections, expected_result",
    [
        pytest.param(
            """
            <TransXChange>
            <Routes>
                <Route id="R1">
                    <Description>Route 1</Description>
                    <RouteSectionRef>RS1</RouteSectionRef>
                    <RouteSectionRef>RS2</RouteSectionRef>
                </Route>
                <Route id="R2">
                    <Description>Route 2</Description>
                    <RouteSectionRef>RS3</RouteSectionRef>
                </Route>
            </Routes>
            </TransXChange>
            """,
            [
                TXCRouteSection(
                    id="RS1", RouteLink=[TXCRouteLink(id="RL1", From="A", To="B")]
                ),
                TXCRouteSection(
                    id="RS2", RouteLink=[TXCRouteLink(id="RL2", From="B", To="C")]
                ),
                TXCRouteSection(
                    id="RS3", RouteLink=[TXCRouteLink(id="RL3", From="C", To="D")]
                ),
            ],
            [
                TXCRoute(
                    id="R1",
                    Description="Route 1",
                    RouteSectionRef=[
                        TXCRouteSection(
                            id="RS1",
                            RouteLink=[TXCRouteLink(id="RL1", From="A", To="B")],
                        ),
                        TXCRouteSection(
                            id="RS2",
                            RouteLink=[TXCRouteLink(id="RL2", From="B", To="C")],
                        ),
                    ],
                ),
                TXCRoute(
                    id="R2",
                    Description="Route 2",
                    RouteSectionRef=[
                        TXCRouteSection(
                            id="RS3",
                            RouteLink=[TXCRouteLink(id="RL3", From="C", To="D")],
                        ),
                    ],
                ),
            ],
            id="Valid routes",
        ),
        pytest.param(
            """
             <TransXChange>
            <Routes>
                <Route>
                    <Description>Route 1</Description>
                    <RouteSectionRef>RS1</RouteSectionRef>
                </Route>
            </Routes>
             </TransXChange>
            """,
            [
                TXCRouteSection(
                    id="RS1", RouteLink=[TXCRouteLink(id="RL1", From="A", To="B")]
                ),
            ],
            [],
            id="Route missing id",
        ),
        pytest.param(
            """
             <TransXChange>
            <Routes>
                <Route id="R1">
                    <RouteSectionRef>RS1</RouteSectionRef>
                </Route>
            </Routes> 
            </TransXChange>
            """,
            [
                TXCRouteSection(
                    id="RS1", RouteLink=[TXCRouteLink(id="RL1", From="A", To="B")]
                ),
            ],
            [
                TXCRoute(
                    id="R1",
                    Description="MISSING ROUTE DESCRIPTION",
                    RouteSectionRef=[
                        TXCRouteSection(
                            id="RS1",
                            RouteLink=[TXCRouteLink(id="RL1", From="A", To="B")],
                        ),
                    ],
                ),
            ],
            id="Route missing description",
        ),
        pytest.param(
            """
             <TransXChange>
            <Routes>
                <Route id="R1">
                    <Description>Route 1</Description>
                    <RouteSectionRef>RS1</RouteSectionRef>
                    <RouteSectionRef>RS2</RouteSectionRef>
                </Route>
            </Routes>
             </TransXChange>
            """,
            [
                TXCRouteSection(
                    id="RS1", RouteLink=[TXCRouteLink(id="RL1", From="A", To="B")]
                ),
            ],
            [
                TXCRoute(
                    id="R1",
                    Description="Route 1",
                    RouteSectionRef=[
                        TXCRouteSection(
                            id="RS1",
                            RouteLink=[TXCRouteLink(id="RL1", From="A", To="B")],
                        ),
                    ],
                ),
            ],
            id="Route with missing route section",
        ),
        pytest.param(
            """
            <TransXChange>
            </TransXChange>
            """,
            [],
            [],
            id="Missing Routes section",
        ),
    ],
)
def test_parse_routes(
    xml_string: str,
    route_sections: list[TXCRouteSection],
    expected_result: list[TXCRoute],
):
    """
    Test Parsing the routes section
    """

    xml_data = etree.fromstring(xml_string)
    result = parse_routes(xml_data, route_sections)

    assert result == expected_result
