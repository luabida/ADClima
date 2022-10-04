"""
This module is responsible for retrieving the data from Copernicus.
All data collected comes from "ERA5 hourly data on single levels
from 1959 to present" dataset, which can be found here:
https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels
Copernicus allows the user retrieve data in Grib or NetCDF file format,
that contains geolocation data, besides the selected data to be requested
from the API. The data will later be compiled in a single DataFrame that
contains the following data:

date       : datetime object.
geocode    : geocode from a specific brazilian city, according to IBGE format.
temp_min   : Minimum┐
temp_med   : Average├─ temperature in `celcius degrees` given a geocode coordinate.
temp_max   : Maximum┘
precip_min : Minimum┐
precip_med : Average├─ of total precipitation in `mm` given a geocode coordinate.
precip_max : Maximum┘
pressao_min: Minimum┐
pressao_med: Average├─ sea level pressure in `hPa` given a geocode coordinate.
pressao_max: Maximum┘
umid_min   : Minimum┐
umid_med   : Average├─ percentage of relative humidity given a geocode coordinate.
umid_max   : Maximum┘

Data collected for these measures are obtained by retrieving the following
variables from the API:

2m temperature (t2m)
Total precipitation (tp)
Mean sea level pressure (msl)
2m dewpoint temperature (d2m)

Data will be collected within a 3 hour range along each day of the month,
the highest and lowest values are stored and the mean is taken with all
the values from the day.

Methods
-------

    download() : Send a request to Copernicus API with the parameters of
                 the city specified by its geocode. The data can be retrieved
                 for certain day of the year and within a time range. As much
                 bigger the time interval chosen, as long will take to download
                 the requested data.
                 @warning: for some reason, even if requested by Copernicus
                           website, trying to retrieve a date range with the
                           current month and the last days of the past month
                           is not possible. For data with a month range, do
                           not choose the current one.
                 @warning: date 2022-08-01 is corrupting all data retrieved.

    _parse_data(data, columns_name) : Groups data by date and aggregate values
                                      to max, min and avg values.

    _retrieve_data(row) : Uses numpy.mean() to aggregate all data from the four
                          coordinate points collected from a specific geocode
                          coordinate.
                          @see `extract_coodinates` module.

    to_dataframe(file) : Will handle the NetCDF file and retrieve its values
                         using numpy `load_dataset()` method and return a
                         DataFrame with the format above.
"""

import re
import logging
import numpy as np
import pandas as pd
import xarray as xr
import metpy.calc as mpcalc

from pathlib import Path
from functools import reduce
from metpy.units import units
from typing import Optional, Union
from datetime import datetime, timedelta

from cds_weather.extract_coordinates import do_area
from cds_weather import extract_latlons, connection, globals


def download(
    geocode: Optional(Union[int, str]) = None,
    past_date: Optional[str] = None,
    date: Optional[str] = None,
    data_dir: Optional[str] = None,
    uid: Optional[str] = None,
    key: Optional[str] = None,
):
    """
    Creates the request for Copernicus API. Extracts the latitude and
    longitude for a given geocode of a brazilian city, calculates the
    area in which the data will be retrieved and send the request via
    `cdsapi.Client()`. Data can be retrieved for a specific date of
    the year or a date range, usage:

    download(geocode=3304557, date='2022-10-04') or
    download(geocode=3304557, past_date='2022-10-01', date='2022-10-04')

    Using this way, a request will be done to extract the data of the four
    closest coordinates from Rio de Janeiro coordinates, which can be found
    at `municipios.json`. A file in the NetCDF format will be downloaded as
    specified in `data_dir` attribute with the format GEOCODE_PASTDATE_DATE.nc,
    returned as a variable to be used in `to_dataframe()` method.

    Attrs:
        geocode (opt(int or str)): Geocode of a specific city in Brazil,
                                   according to IBGE's format.
        past_date (opt(str)): Format 'YYYY-MM-DD'. Used along with `date`
                              to define a date range.
        date (opt(str)): Format 'YYYY-MM-DD'. Date of data to be retrieved.
        data_dir (opt(str)): Path in which the NetCDF file will be downloaded.
                             Default directory is specified in `globals.DATA_DIR`.
        uid (opt(str)): UID from Copernicus User page, it will be used with
                        `connection.connect()` method.
        key (opt(str)): API Key from Copernicus User page, it will be used with
                        `connection.connect()` method.

    Returns:
        `data_dir/filename` that can later be used to transform into DataFrame
        with `to_dataframe()` method.
    """

    help = "Use `help(extract_reanalysis.download())` for more info."
    conn = connection.connect(uid, key)
    format = "%Y-%m-%d"
    iso_format = "YYYY-MM-DD"
    re_format = r"\d{4}-\d{2}-\d{2}"
    today = datetime.now()

    if data_dir:
        data_dir = Path(str(data_dir))
        data_dir.mkdir(parents=True, exist_ok=True)

    if not data_dir:
        data_dir = globals.DATA_DIR

    if date:
        ini_date = datetime.strptime(date, format)
        year, month, day = date.split("-")
        filename = f'{geocode}_{date.replace("-","")}.nc'
        # dataset has maximum of 7 days of update delay.
        # in order to prevent requesting invalid dates,
        # the max date is 7 days from today's date
        max_update_delay = today - timedelta(days=7)
        if ini_date > max_update_delay:
            raise Exception(
                f"""
                    Invalid date. The last update date is:
                    {datetime.strftime(max_update_delay, format)}
                    {help}
            """
            )

        # check for right initial date format
        if not re.match(re_format, date):
            return logging.error(
                f"""
                    Invalid initial date. Format:
                    {iso_format}
                    {help}
            """
            )

        # an end date can be passed to define the date range
        # if there is no end date, only the day specified on
        # `date` will be downloaded
        if past_date:
            end_date = datetime.strptime(past_date, format)

            # check for right end date format
            if not re.match(re_format, past_date):
                return logging.error(
                    f"""
                        Invalid end date. Format:
                        {iso_format}
                        {help}
                """
                )

            # safety limit for Copernicus limit and file size: 2 years
            max_api_query = timedelta(days=731)
            if ini_date - end_date > max_api_query:
                return logging.error(
                    f"""
                        Maximum query reached.
                        {help}
                """
                )

            # end date can't be bigger than initial date
            if end_date >= ini_date:
                return logging.error(
                    f"""
                        Past date can't be more recent than the initial date.
                        {help}
                """
                )

            filename = f"{geocode}_{past_date}_{date}.nc"
            filename = filename.replace("-", "")

            # the date range will be responsible for match the requests
            # if the date is across months. For example a week that ends
            # after the month.
            df = pd.date_range(start=past_date, end=date)
            year_set = set()
            month_set = set()
            day_set = set()
            for date in df:
                date_f = str(date)
                iso_form = date_f.split(" ")[0]
                year_, month_, day_ = iso_form.split("-")
                year_set.add(year_)
                month_set.add(month_)
                day_set.add(day_)

            # parsing the correct types
            month = list(month_set)
            day = list(day_set)
            day.sort()
            if len(year_set) == 1:
                year = str(list(year_set)[0])
            else:
                year = list(year)

    else:
        raise Exception(
            f"""
            Bad usage.
            {help}
        """
        )

    try:
        lat, lon = extract_latlons.from_geocode(geocode)
        north, south, east, west = do_area(lat, lon)

        conn.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "variable": [
                    "2m_temperature",
                    "total_precipitation",
                    "2m_dewpoint_temperature",
                    "mean_sea_level_pressure",
                ],
                "year": year,
                "month": month,
                "day": day,
                "time": [
                    "00:00",
                    "03:00",
                    "06:00",
                    "09:00",
                    "12:00",
                    "15:00",
                    "18:00",
                    "21:00",
                ],
                "area": [
                    north,
                    west,
                    south,
                    east,
                ],
                "format": "netcdf",
            },
            f"{data_dir}/{filename}",
        )
        logging.info(f"NetCDF {filename} downloaded at {data_dir}.")

        return f"{data_dir}/{filename}"

    except Exception as e:
        logging.error(e)


def _parse_data(data, column_name):
    df = pd.DataFrame(data)
    df["date"] = df["date"].dt.floor("D")
    result = df.groupby("date").agg(
        var_min=("var", "min"), var_med=("var", "mean"), var_max=("var", "max")
    )

    result.columns = result.columns.str.replace("var", column_name)
    return result


def _retrieve_data(row):
    parsed_date = row.time.values.astype("M8[ms]").astype("O")
    avg_vals = np.mean(row.values)
    return dict(date=parsed_date, var=avg_vals)


def to_dataframe(file):
    # Load netCDF file into xarray dataset
    ds = xr.load_dataset(file, engine="netcdf4")
    geocode = file.split("/")[-1].split("_")[0]

    # Parse units to br's units
    t2m = ds.t2m - 273.15
    tp = ds.tp * 1000
    msl = ds.msl / 100
    d2m = ds.d2m - 273.15
    # relative_humidity = temperature/dewpoint_temperature
    rh = (
        mpcalc.relative_humidity_from_dewpoint(t2m * units.degC, d2m * units.degC) * 100
    )

    temperature = _parse_data([_retrieve_data(v) for v in t2m], "temp")
    precipitation = _parse_data([_retrieve_data(v) for v in tp], "precip")
    rel_hum = _parse_data([_retrieve_data(v) for v in rh], "umid")
    pressure = _parse_data([_retrieve_data(v) for v in msl], "pressao")

    dfs = [temperature, precipitation, pressure, rel_hum]
    merged_dfs = reduce(lambda l, r: pd.merge(l, r, on=["date"]), dfs)

    geocodes = [geocode for r in range(len(merged_dfs))]
    merged_dfs.insert(0, "geocodigo", geocodes)
    return merged_dfs
