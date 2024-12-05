class NoSchemaDefinition(Exception):
    code = "NO_SCHEMA_FOUND"
    message_template = "No schema found for category {category}."

    def __init__(self, category, line=1, message=None):
        self.category = category
        if message is None:
            self.message = self.message_template.format(category=category)
        else:
            self.message = message
        self.line = line
