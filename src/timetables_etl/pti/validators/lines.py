from collections import defaultdict
import itertools

from pti.validators.base import BaseValidator


# TODO: Finish class implementation + move tests
class LinesValidator(BaseValidator):
    def __init__(self, *args, stop_area_map=None, **kwargs):
        self._stop_area_map = stop_area_map or {}
        super().__init__(*args, **kwargs)