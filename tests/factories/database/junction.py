import factory
from common_layer.database.models import TransmodelServicePatternTracks


class TransmodelServicePatternTracksFactory(factory.Factory):
    """Factory for TransmodelTracks"""

    class Meta:  # type: ignore[misc]
        model = TransmodelServicePatternTracks

    service_pattern_id = None
    tracks_id = None
    sequence_number = factory.Sequence(lambda n: n + 1)

    @classmethod
    def create_with_id(cls, id_number: int, **kwargs) -> TransmodelServicePatternTracks:
        """Creates a TransmodelTrack with a specific ID"""
        service_pattern_track = cls.create(**kwargs)
        service_pattern_track.id = id_number
        return service_pattern_track
