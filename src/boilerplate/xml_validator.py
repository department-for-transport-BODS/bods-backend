from defusedxml import DefusedXmlException, ElementTree as detree
from lxml import etree
from exceptions.xml_file_exceptions import FileTooLarge, XMLSyntaxError, DangerousXML
from logger import logger
from bods_utils import get_file_size


class FileValidator:
    def __init__(self, source, max_file_size=10e9):
        self.source = source
        if self.is_file:
            self.source.seek(0)
        self.max_file_size = max_file_size

    @property
    def is_file(self):
        return hasattr(self.source, "seek")

    def is_too_large(self):
        if self.is_file:
            size_ = get_file_size(self.source)
        else:
            with open(self.source, "rb") as f_:
                size_ = get_file_size(f_)

        return size_ > self.max_file_size

    def validate(self):
        """Validates the file.

        Raises:
            FileTooLarge: if file size is greater than max_file_size.
        """
        if self.is_too_large():
            raise FileTooLarge(self.source.name)


class XMLValidator(FileValidator):
    """Class for validating a XML file.

    Args:
        file (File): A file-like object.
        max_file_size (int): The max file size allowed. default is 1 Gigabyte.

    Examples:
        >>> f = open("./path/to/xml/file.xml", "rb")
        >>> validator = XMLValidator(f)
        >>> validator.is_too_large()
            False
        >>> validator.validate()
        >>> f.close()
    """

    def __init__(self, source, max_file_size=5e9, schema=None):
        super().__init__(source, max_file_size=max_file_size)
        self.schema = schema
        self.violations = []

    def dangerous_xml_check(self):
        try:
            detree.parse(
                self.source, forbid_dtd=True, forbid_entities=True, forbid_external=True
            )
        except detree.ParseError as err:
            # DefusedXml wraps ExpatErrors in ParseErrors, requires extra step to
            # get actual error message
            if isinstance(err.msg, Exception):
                self.violations.append(
                    XMLSyntaxError(self.source.name, message=err.msg.args[0])
                )
            else:
                self.violations.append(
                    XMLSyntaxError(self.source.name, message=err.msg, line=err.lineno)
                )
        except DefusedXmlException:
            self.violations.append(DangerousXML(self.source.name))
        return self.violations

    def validate(self):
        """Validates the XML file.

        Raises:
            FileTooLarge: if file size is greater than max_file_size.
            DangerousXML: if DefusedXmlException is raised during parsing.
            XMLSyntaxError: if the file cannot be parsed.
        """
        if self.is_too_large():
            self.violations.append(FileTooLarge(self.source.name))
            return self.violations
        if len(self.dangerous_xml_check()) > 0:
            return self.violations
        return self.validate_xml()

    def validate_xml(self):
        """Parses `file` returning an lxml element object.
        If `schema` is not None then `file` is validated against the schema.

        Returns:
           doc(_ElementTree): an lxml element tree representing the document.

        Raises:
            lxml.XMLSyntaxError: if contents of `file` do not match the `schema`
        """
        if self.is_file:
            self.source.seek(0)
        parser = None
        if self.schema is not None:
            lxml_schema = get_lxml_schema(self.schema)
            parser = etree.XMLParser(schema=lxml_schema)
        try:
            doc = etree.parse(self.source, parser)
        except etree.XMLSyntaxError as err:
            self.violations.append(
                XMLSyntaxError(self.source.name, message=err.msg, line=err.lineno)
            )
        return self.violations


def get_lxml_schema(schema):
    """Creates an lxml XMLSchema object from a file, file path or url."""
    if schema is None:
        return

    if not isinstance(schema, etree.XMLSchema):
        logger.info(f"[XML] => Parsing {schema}.")
        root = etree.parse(schema)
        schema = etree.XMLSchema(root)
    return schema
