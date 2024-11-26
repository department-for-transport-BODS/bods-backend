from lxml import etree
from pti.models import VehicleJourney

def test_vehicle_journey_from_xml():
    """
    Test `from_xml` method for the VehicleJourney model.
    """
    # Mock XML string representing a VehicleJourney
    xml_string = """
    <VehicleJourney xmlns="http://www.example.com">
        <VehicleJourneyCode>VJ123</VehicleJourneyCode>
        <LineRef>Line456</LineRef>
        <JourneyPatternRef>JP789</JourneyPatternRef>
        <VehicleJourneyRef>VJREF012</VehicleJourneyRef>
        <ServiceRef>Service345</ServiceRef>
    </VehicleJourney>
    """
    
    # Parse the XML string into an lxml element
    root = etree.fromstring(xml_string)

    # Expected values
    expected_data = {
        "code": "VJ123",
        "line_ref": "Line456",
        "journey_pattern_ref": "JP789",
        "vehicle_journey_ref": "VJREF012",
        "service_ref": "Service345",
    }

    vehicle_journey = VehicleJourney.from_xml(root)

    assert vehicle_journey.model_dump() == expected_data