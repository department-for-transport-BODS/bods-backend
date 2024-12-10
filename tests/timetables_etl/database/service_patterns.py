"""
Implement Service Patterns
"""

from pathlib import Path

import pandas as pd
from geoalchemy2.shape import from_shape
from shapely.wkt import loads as wkt_loads

from timetables_etl.app.database.models.model_transmodel import TransmodelServicePattern


def load_service_patterns_from_csv(
    csv_path: Path | str,
) -> list[TransmodelServicePattern]:
    """Load TransmodelServicePattern instances from CSV file"""
    df = pd.read_csv(csv_path)

    patterns = []
    for _, row in df.iterrows():
        line = wkt_loads(row["geom"])
        patterns.append(
            TransmodelServicePattern(
                service_pattern_id=row["service_pattern_id"],
                origin=row["origin"] or "",
                destination=row["destination"] or "",
                description=row["description"],
                geom=from_shape(line, srid=4326),
                revision_id=row["revision_id"],
                line_name=row["line_name"],
            )
        )
    return patterns
