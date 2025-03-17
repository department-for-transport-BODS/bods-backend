from pathlib import Path

from common_layer.dynamodb.models import FaresViolation

from fares_etl.validation.app.fares_validator import FaresValidator

DATA_DIR = Path(__file__).parent / "test_data"


def test_fares_validator_with_no_violations():
    filepath = DATA_DIR / "fares_test_xml_pass.xml"
    fares_validator = FaresValidator()

    with open(filepath, "rb") as f:
        result = fares_validator.get_violations(f)
        assert result == []


def test_fares_validator_with_violations():
    filepath = DATA_DIR / "fares_test_xml_fail.xml"
    fares_validator = FaresValidator()

    with open(filepath, "rb") as f:
        result = fares_validator.get_violations(f)
        assert result == [
            FaresViolation(
                line=1819,
                observation="Element 'TripType' is missing within 'RoundTrip'",
                category="Conditions",
            ),
        ]
