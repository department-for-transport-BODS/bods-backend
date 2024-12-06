class NoRowFound(Exception):
    code = "NO_ROW_FOUND"
    message_template = "No row found for {field_name} {field_value} in database."

    def __init__(self, field_name, field_value, line=1, message=None):
        self.field_name = field_name
        self.field_value = field_value
        if message is None:
            self.message = self.message_template.format(
                field_name=field_name, field_value=field_value
            )
        else:
            self.message = message
        self.line = line
