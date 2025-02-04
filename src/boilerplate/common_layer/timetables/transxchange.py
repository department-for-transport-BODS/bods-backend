"""
TranXChangeElement currently used by PTI
"""

from common_layer.xmlelements import XMLElement
from structlog.stdlib import get_logger

log = get_logger()
GRID_LOCATION = "Grid"
WSG84_LOCATION = "WGS84"
PRINCIPAL_TIMING_POINTS = ["PTP", "principalTimingPoint"]
TRANSXCAHNGE_NAMESPACE = "http://www.transxchange.org.uk/"
TRANSXCHANGE_NAMESPACE_PREFIX = "x"


class TransXChangeElement(XMLElement):
    """A wrapper class to easily work lxml elements for TransXChange XML.

    This adds the TransXChange namespaces to the XMLElement class.
    The TransXChangeDocument tree is traversed using the following general
    principle. Child elements are accessed via properties, e.g.
    Service elements are document.services.

    If you expect a bultin type to be returned this will generally
    be a getter method e.g. documents.get_scheduled_stop_points_ids()
    since this returns a list of strings.

    Args:
        root (etree._Element): the root of an lxml _Element.

    Example:
        # Traverse the tree
        tree = etree.parse(netexfile)
        trans = TransXChangeDocument(tree.getroot())
        trans.get_element("PublicationTimestamp")
            PublicationTimestamp(text='2119-06-22T13:51:43.044Z')
        trans.get_elements(["dataObjects", "CompositeFrame"])
            [CompositeFrame(...), CompositeFrame(...)]
        trans.get_elements(["dataObjects", "CompositeFrame", "Name"])
            [Name(...), Name(...)

        # Element attributes are accessed like dict values
        trans["version"]
            '1.1'
    """

    namespaces = {TRANSXCHANGE_NAMESPACE_PREFIX: TRANSXCAHNGE_NAMESPACE}

    def _make_xpath(self, xpath):
        if isinstance(xpath, (list, tuple)):
            xpath = [TRANSXCHANGE_NAMESPACE_PREFIX + ":" + path for path in xpath]
        else:
            xpath = TRANSXCHANGE_NAMESPACE_PREFIX + ":" + xpath
        return super()._make_xpath(xpath)
