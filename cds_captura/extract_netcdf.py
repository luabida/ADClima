from typing import Optional, Union, Dict
import logging
import pandas as pd
from datetime import datetime, timedelta
import re
import extract_latlons
from extract_coordinates import do_area
import connection


def download(geocode: Optional[int] = None,
             city_name: Optional[int] = None,
             past_date: Optional[str] = None,
             date: Optional[str] = None,
             uid: Optional[str] = None,
             key: Optional[str] = None
            ):
    """


    """

    conn = connection.connect(uid, key)
    format = '%Y-%m-%d'
    iso_format = 'YYYY-MM-DD'
    re_format = r'\d{4}-\d{2}-\d{2}'
    today = datetime.now()


    if geocode:
        try:
            lat, lon = extract_latlons.from_geocode(geocode)
            north, south, east, west = do_area(lat, lon)
        except Exception as e:
            logging.error(f'{geocode} not found. Please use a valid Geocode.')

    if city_name:
        lat, lon, geocode = extract_latlons.from_city_name(city_name)
        north, south, east, west = do_area(lat, lon)

    if date:
        ini_date = datetime.strptime(date, format)
        year, month, day = date.split('-')
        filename = f'{geocode}_{date.replace("-","")}.nc'
        # dataset has maximum of 7 days of update delay.
        # in order to prevent requesting invalid dates,
        # the max date is 7 days from today's date
        max_update_delay = today - timedelta(days=7)
        if ini_date > max_update_delay:
            raise Exception(f"""
                    Invalid date. The last update date is:
                    {datetime.strftime(max_update_delay, format)}
                    {help}
            """)


        # check for right initial date format
        if not re.match(re_format, date):
            return logging.error(f'''
                    Invalid initial date. Format:
                    {iso_format}
                    {help}
            ''')

        # an end date can be passed to define the date range
        # if there is no end date, only the day specified on
        # @param `ini` will be downloaded
        if past_date:
            end_date = datetime.strptime(past_date, format)

            # check for right end date format
            if not re.match(re_format, past_date):
                return logging.error(f'''
                        Invalid end date. Format:
                        {iso_format}
                        {help}
                ''')

            # safety limit for Copernicus limit and file size: 2 years
            max_api_query = timedelta(days=731)
            if ini_date - end_date > max_api_query:
                return logging.error(f'''
                        Maximum query reached.
                        {help}
                ''')


            # end date can't be bigger than initial date
            if end_date >= ini_date:
                return logging.error(f'''
                        Past date can't be more recent than the initial date.
                        {help}
                ''')

            filename = f'{geocode}_{past_date}_{date}.nc'
            filename = filename.replace('-','')

            # the date range will be responsible for match the requests
            # if the date is across months. For example a week that ends
            # after the month.
            #
            # the sets prevent duplicated dates, but also shuffles the days (!)
            df = pd.date_range(start=past_date, end=date)
            year_set = set()
            month_set = set()
            day_set = set()
            for date in df:
                date_f = str(date)
                iso_form = date_f.split(' ')[0]
                year_, month_, day_ = iso_form.split('-')
                year_set.add(year_)
                month_set.add(month_)
                day_set.add(day_)

            # parsing the correct types
            month = list(month_set)
            day = list(day_set)
            if len(year_set) == 1:
                year = str(list(year_set)[0])
            else:
                year = list(year)

    else:
        raise Exception(f"""
            Bad usage.
            {help}
        """)

    try:
        conn.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'variable': [
                    '2m_temperature',
                    'total_precipitation',
                    '2m_dewpoint_temperature',
                    'mean_sea_level_pressure',
                ],
                'year': year,
                'month': month,
                'day': day,
                'time': [
                    '00:00', '03:00', '06:00',
                    '09:00', '12:00', '15:00',
                    '18:00', '21:00',
                ],
                'area': [
                    north, west, south,
                    east,
                ],
                'format': 'netcdf',
            },
            f'data/{filename}')
        logging.info(f'NetCDF {filename} downloaded.')

    except Exception as e:
        logging.error(e)
