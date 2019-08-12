#! /usr/bin/env python
# -*- coding: utf-8 -*-
import time
import us
import pathlib
import zipfile
import geopandas as gpd
from urllib.request import urlretrieve

# Logging
import logging
logger = logging.getLogger(__name__)


class BaseDownloader(object):
    THIS_DIR = pathlib.Path(__file__).parent
    PARENT_DIR = THIS_DIR.parent

    def __init__(self, data_dir=None):
        # Set the download directory
        if data_dir:
            self.data_dir = pathlib.Path(str(data_dir))
        else:
            self.data_dir = self.PARENT_DIR.joinpath("data")

        # Initialize all the directories we will need
        if not self.data_dir.exists():
            self.data_dir.mkdir()
        self.raw_dir = self.data_dir.joinpath("raw")
        if not self.raw_dir.exists():
            self.raw_dir.mkdir()
        self.processed_dir = self.data_dir.joinpath("processed")
        if not self.processed_dir.exists():
            self.processed_dir.mkdir()

    @property
    def shp_name(self):
        return self.zip_name.replace(".zip", ".shp")

    @property
    def shp_path(self):
        return self.raw_dir.joinpath(self.shp_name)

    @property
    def zip_path(self):
        return self.raw_dir.joinpath(self.zip_name)

    @property
    def geojson_path(self):
        return self.processed_dir.joinpath(self.geojson_name)

    @property
    def geojson_name(self):
        return f'{self.PROCESSED_NAME}.geojson'

    def run(self):
        self.download()
        self.unzip()
        self.process()

    def download(self):
        """
        Downloads the TIGER SHP file of Census block for the provided state and county.
        Returns the path to the ZIP file.
        """
        # Check if the zip file already exists
        if self.zip_path.exists():
            logger.debug(f"ZIP file already exists at {self.zip_path}")
            return

        # If it doesn't, download it from the Census FTP
        logger.debug(f"Downloading {self.url} to {self.zip_path}")
        urlretrieve(self.url, self.zip_path)
        time.sleep(1)

    def unzip(self):
        """
        Unzip the provided ZIP file.
        """
        # Check if the shape has already been unzipped
        if self.shp_path.exists():
            logger.debug(f"SHP already unzipped at {self.shp_path}")
            return

        # If not, unzip it now.
        logger.debug(f"Unzipping {self.zip_path} to {self.raw_dir}")
        with zipfile.ZipFile(self.zip_path, "r") as z:
            z.extractall(self.raw_dir)

    def process(self):
        """
        Refine the raw data and convert it to our preferred format, GeoJSON.
        """
        # Check if the geojson file already exists
        if self.geojson_path.exists():
            logger.debug(f"GeoJSON file already exists at {self.geojson_path}")
            return

        gdf = gpd.read_file(self.shp_path)

        trimmed = gdf[list(self.FIELD_CROSSWALK.keys())]

        # Rename the fields using the crosswalk as a map
        trimmed.rename(columns=self.FIELD_CROSSWALK, inplace=True)

        # Write out GeoJSON file
        logger.debug(f"Writing out {len(gdf)} shapes to {self.geojson_path}")
        trimmed.to_file(self.geojson_path, driver="GeoJSON")


class BaseStateDownloader(BaseDownloader):
    """
    A base downloader for a single state's source files.
    """
    def __init__(self, state, data_dir):
        # Configure the state
        self.state = us.states.lookup(state)
        super().__init__(data_dir)

    @property
    def geojson_name(self):
        return f"{self.PROCESSED_NAME}_{self.state.abbr.upper()}.geojson"
