from typing import IO, Any


class PTIValidator:
    def __init__(self, source: IO[Any]):
        self.violations = []
        # TODO: Load schema & add function registration

    def is_valid(self, source: IO[Any]) -> bool:
        raise NotImplementedError()