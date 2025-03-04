"""
CodeSpace Parsing functions
"""

from lxml.etree import _Element  # type: ignore
from structlog.stdlib import get_logger

from ....utils import get_tag_name, parse_xml_attribute
from ...models import Codespace, CodespaceRef
from ..netex_utility import get_netex_text, parse_multilingual_string

log = get_logger()


def parse_codespaces(elem: _Element) -> list[CodespaceRef | Codespace]:
    """
    Parse Codespaces or CodespaceRef List
    """
    codespaces: list[CodespaceRef | Codespace] = []
    for child in elem:
        tag = get_tag_name(child)
        match tag:
            case "CodespaceRef":
                codespace_ref = parse_xml_attribute(child, "ref")
                if not codespace_ref:
                    log.warning("Codespace Ref missing Id")
                    continue
                codespaces.append(CodespaceRef(ref=codespace_ref))
            case "Codespace":
                codespace_id = parse_xml_attribute(child, "id")
                xmlns = get_netex_text(child, "Xmlns")
                if not codespace_id or not xmlns:
                    log.info(
                        "Codespace missing id or xmlns",
                        codespace_id=codespace_id,
                        xmlns=xmlns,
                    )
                    continue
                codespaces.append(
                    Codespace(
                        id=codespace_id,
                        Xmlns=xmlns,
                        XmlnsUrl=get_netex_text(child, "XmlnsUrl"),
                        Description=parse_multilingual_string(child, "Description"),
                    )
                )
            case _:
                log.warning("Not a CodespaceRef or Codespace in Codespaces Section")
    return codespaces
