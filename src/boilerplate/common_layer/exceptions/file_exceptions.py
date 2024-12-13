# Exception for File Processing
class ValidationException(Exception):
    code = "VALIDATION_FAILED"
    message_template = "Validation failed for {filename}."

    def __init__(self, filename, line=1, message=None):
        self.filename = filename
        if message is None:
            self.message = self.message_template.format(filename=filename)
        else:
            self.message = message
        self.line = line

    def __str__(self):
        return (f"[{self.code}] {self.message} "
                f"(File: {self.filename}, Line: {self.line})")


class AntiVirusError(ValidationException):
    """Base exception for antivirus scans."""

    code = "ANTIVIRUS_FAILURE"
    message_template = "Antivirus failed validating file {filename}."


class SuspiciousFile(AntiVirusError):
    """Exception for when a suspicious file is found."""

    code = "SUSPICIOUS_FILE"
    message_template = "Anti-virus alert triggered for file {filename}."


class ClamConnectionError(AntiVirusError):
    """Exception for when we can't connect to the ClamAV server."""

    code = "AV_CONNECTION_ERROR"
    message_template = "Could not connect to Clam daemon when \
                        testing {filename}."
