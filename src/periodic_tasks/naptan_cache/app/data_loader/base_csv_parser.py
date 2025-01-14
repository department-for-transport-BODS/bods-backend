"""
Base Class for parsing data
"""

from abc import ABC, abstractmethod
from datetime import datetime
from functools import cached_property
from pathlib import Path

import pandas as pd
from structlog.stdlib import get_logger

from .file_utils import create_data_dir

log = get_logger()


class BaseCSVParser(ABC):
    """
    Abstract Base Class for implementing CSV parsing and querying
    """

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or self._find_default_data_dir()
        self.data_dir = create_data_dir(self.data_dir)

        self.check_data_timestamp()
        self.load_data()

    @property
    @abstractmethod
    def csv_files(self) -> list[str]:
        """
        The list of CSV files to query for
        """

    @abstractmethod
    def _find_default_data_dir(self) -> Path:
        """
        Returns the default data path
        """

    @abstractmethod
    def download_data(self):
        """
        Abstract method to download the data files.
        """

    @abstractmethod
    def read_csv(self, file_path: Path) -> pd.DataFrame:
        """
        Abstract method to read a CSV file.
        Since it's possible to use faster pyarrow
        But the bus registrations is multi-line csv so needs own implementation
        """

    def load_data(self):
        """Load the data"""
        try:
            self.dataframes
        except FileNotFoundError as e:
            log.warning("Data not found: %s", str(e))

    def _update_timestamp(self):
        """
        Update the timestamp file with the current date and time.
        """
        timestamp_file = self.data_dir / "last_fetched.txt"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(timestamp_file, "w", encoding="utf-8") as file:
            file.write(current_time)

    def check_data_timestamp(self, max_age: int = 7):
        """
        Check the timestamp of the data files
        Redownload if older than the specified maximum age (in days).
        """
        timestamp_file = self.data_dir / "last_fetched.txt"

        if timestamp_file.exists():
            with open(timestamp_file, "r", encoding="utf-8") as file:
                last_fetched = file.read().strip()

            last_fetched_time = datetime.strptime(last_fetched, "%Y-%m-%d %H:%M:%S")
            current_time = datetime.now()
            time_diff = current_time - last_fetched_time

            if time_diff.days >= max_age:
                log.info(
                    "Data files are older than max age. Redownloading data.",
                    parser=self.__class__.__name__,
                    max_age_days=max_age,
                )
                self.download_data()
                self._update_timestamp()
            else:
                # Check if all CSV files exist
                missing_files = [
                    file
                    for file in self.csv_files
                    if not (self.data_dir / file).exists()
                ]
                if missing_files:
                    log.info(
                        "Some CSV files are missing. Redownloading data.",
                        missing_files=missing_files,
                        parser=self.__class__.__name__,
                    )
                    self.download_data()
                    self._update_timestamp()
                else:
                    log.info(
                        "Data files are up to date.",
                        parser=self.__class__.__name__,
                        last_fetched=last_fetched,
                        max_age_days=max_age,
                    )
        else:
            log.info(
                "Data files not found. Downloading data.",
                parser=self.__class__.__name__,
            )
            self.download_data()
            self._update_timestamp()

    @cached_property
    def dataframes(self) -> dict[str, pd.DataFrame]:
        """
        Load DataFrames
        """
        dataframes: dict[str, pd.DataFrame] = {}
        for file in self.csv_files:
            file_path = self.data_dir / file
            if not file_path.exists():
                raise FileNotFoundError(
                    f"CSV file '{file}' not found in the data directory."
                )

            df = self.read_csv(file_path)
            dataframes[file.split(".", maxsplit=1)[0]] = df
            relative_path = file_path.relative_to(self.data_dir)
            log.info(
                "Parsed CSV Data",
                path=str(relative_path),
                parser=self.__class__.__name__,
                row_count=len(df),
            )
        return dataframes
