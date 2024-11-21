from io import StringIO


class JSONFile(StringIO):
    def __init__(self, str_, **kwargs):
        super().__init__(**kwargs)
        self.write(str_)
        self.seek(0)
        self.name = "pti_schema.json"
