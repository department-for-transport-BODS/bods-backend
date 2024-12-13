"""
Custom Base Model with Configs
"""

from pydantic import BaseModel, ConfigDict


class FrozenBaseModel(BaseModel):
    """
    generates a __hash__() method for model
    """

    model_config = ConfigDict(frozen=True)
