"""
Parse Naptan data for official stop data
"""

from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy.spatial import KDTree
from structlog.stdlib import get_logger

from .base_csv_parser import BaseCSVParser
from .download import download_file

log = get_logger()


def strict_string_conversion(val):
    """
    Ensure all parsed values are strings
    """
    if pd.isna(val):
        return ""
    if isinstance(val, np.integer):
        return str(int(val))
    if isinstance(val, float):
        return str(int(val)) if val.is_integer() else str(val)
    return str(val)


class NaptanData(BaseModel):
    """
    Row Data fetched from NAPTAN Stops List
    """

    ATCOCode: str
    NaptanCode: str
    PlateCode: str
    CleardownCode: str
    CommonName: str
    CommonNameLang: str
    ShortCommonName: str
    ShortCommonNameLang: str
    Landmark: str
    LandmarkLang: str
    Street: str
    StreetLang: str
    Crossing: str
    CrossingLang: str
    Indicator: str
    IndicatorLang: str
    Bearing: str
    NptgLocalityCode: str
    LocalityName: str
    ParentLocalityName: str
    GrandParentLocalityName: str
    Town: str
    TownLang: str
    Suburb: str
    SuburbLang: str
    LocalityCentre: str
    GridType: str
    Easting: str
    Northing: str
    Longitude: str
    Latitude: str
    StopType: str
    BusStopType: str
    TimingStatus: str
    DefaultWaitTime: str
    Notes: str
    NotesLang: str
    AdministrativeAreaCode: str
    CreationDateTime: str
    ModificationDateTime: str
    RevisionNumber: str
    Modification: str
    Status: str


class NaptanParser(BaseCSVParser):
    """
    Parsing and Queries for the Naptan Dataset
    """

    def __init__(self, data_dir: Path | None = None):
        super().__init__(data_dir)
        self.data = self._load_data()
        self.naptan_data_cache: dict[str, NaptanData | None] = {}
        self.filtered_data = self._filter_data()
        self.uk_stop_index: KDTree = self.build_stop_index(self.filtered_data)

    @property
    def csv_files(self) -> list[str]:
        files = ["Stops.csv"]
        return files

    def _find_default_data_dir(self) -> Path:
        current_dir = Path(__file__).resolve().parent
        return current_dir.parent.parent.parent / "data" / "reference" / "naptan"

    def download_data(self):
        # The API CSV potentially has newer data compared to the webpage download url
        # uk_url = "https://beta-naptan.dft.gov.uk/Download/National/csv"
        uk_url = "https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=CSV"

        allowed_extensions = [".csv", ".xlsx"]

        try:
            log.info("Downloading UK Naptan Stops CSV", url=uk_url)
            uk_path = download_file(uk_url, allowed_extensions, self.data_dir)
            log.info("Successfully downloaded UK Stops CSV", path=uk_path)

        except RuntimeError:
            log.error("Error occurred while downloading files", exc_info=True)

    def _load_data(self) -> pd.DataFrame:
        uk_path = self.data_dir / "Stops.csv"
        log.info("Loading UK Naptan Stops", path=uk_path)
        uk_data = self.read_csv(uk_path)
        log.info("UK Naptan Stops Loaded", count=len(uk_data))

        log.info("Sucessfully loaded Naptan Data")
        return uk_data

    def _filter_data(self) -> pd.DataFrame:
        uk_filtered = self.data[
            (self.data["Easting"] != "")
            & (self.data["Northing"] != "")
            & (self.data["Modification"] != "delete")
            & (self.data["Status"] != "inactive")
        ]

        log.info(
            "Filtered UK Data to remove Missing Easting/Northings, Delete/Inactive",
            original=len(self.data),
            filtered=len(uk_filtered),
        )

        return uk_filtered

    def read_csv(self, file_path: Path) -> pd.DataFrame:
        """
        Read CSV or Excel file based on the file extension.
        """
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(
                file_path,
                dtype=str,
                na_filter=False,
                encoding="utf-8",
            )
            return df.set_index("ATCOCode")

        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    def build_stop_index(self, data: pd.DataFrame) -> KDTree:
        """
        Build the stop index using KDTree based on easting and northing
        """
        coordinates: np.ndarray = data[["Easting", "Northing"]].astype(float).values
        return KDTree(coordinates)

    def get_naptan_data_by_atco_code(self, atco_code: str) -> NaptanData | None:
        """
        Get NaptanData instance by ATCOCode
        """
        if atco_code in self.naptan_data_cache:
            return self.naptan_data_cache[atco_code]

        try:
            record = cast(dict[str, str], self.data.loc[atco_code].to_dict())
        except KeyError:
            log.warning("Could Not Find NAPTAN data", ATCOCode=atco_code)
            return None

        record["ATCOCode"] = atco_code
        naptan_data = NaptanData(**record)
        self.naptan_data_cache[atco_code] = naptan_data

        return naptan_data

    def get_nearest_stop_by_coordinates(
        self, easting: str, northing: str
    ) -> NaptanData | None:
        """
        Get the nearest stop by easting and northing coordinates (UK data)
        """
        if self.uk_stop_index.n == 0:
            log.warning("No valid coordinates found in the UK data")
            return None

        coordinates: np.ndarray = np.array([[float(easting), float(northing)]])
        _distances, indices = self.uk_stop_index.query(coordinates, k=1)
        # Extract the scalar index value from the numpy array
        nearest_idx = indices.item()
        nearest_row = self.filtered_data.iloc[nearest_idx]

        # Handle the type conversion safely
        atco_code = nearest_row.name
        if atco_code is None:
            log.warning("Found row has no ATCOCode")
            return None
        if not isinstance(atco_code, str):
            atco_code = str(atco_code)

        return self.get_naptan_data_by_atco_code(atco_code)

    def log_missing_coordinates(self):
        """
        Log the counts of missing latitude, longitude, or both values in the data
        """
        missing_lat = (self.data["Latitude"] == "").sum()
        missing_long = (self.data["Longitude"] == "").sum()
        missing_both = (
            (self.data["Latitude"] == "") & (self.data["Longitude"] == "")
        ).sum()

        log.info(
            "Stops with Missing Lat/Long Found",
            missing_lat=missing_lat,
            missing_long=missing_long,
            missing_both=missing_both,
        )

    def log_missing_ings(self):
        """
        Log the counts of missing easting, northing, or both values in the data
        """
        missing_easting = (self.data["Easting"] == "").sum()
        missing_northing = (self.data["Northing"] == "").sum()
        missing_both = (
            (self.data["Easting"] == "") & (self.data["Northing"] == "")
        ).sum()

        log.info(
            "Stops with Missing Easting/Northing Found",
            missing_easting=missing_easting,
            missing_northing=missing_northing,
            missing_both=missing_both,
        )
