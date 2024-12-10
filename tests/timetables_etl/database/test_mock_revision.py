"""
Test Mock Revision Generation
"""


def test_mock_revision_generation(mock_revision):
    """
    Test Generating a mock revision
    """
    assert mock_revision.id == 3941
    assert mock_revision.name == "Dev Org_Three Mile Cross_UK045_20241111"
