import factory
from common_layer.database.models.model_ui import UiLta


class UiLtaFactory(factory.Factory):
    """
    Factory for creating UiLta instances using the repository pattern.
    """

    class Meta:  # type: ignore
        model = UiLta

    name = factory.Sequence(lambda n: f"LTA{n}")
