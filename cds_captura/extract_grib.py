from typing import Optional, Union, Dict
import cdsapi
import uuid
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import re

# Client is responsible for create the connection with cdsapi
# receives:
#   UID -> int, 6 digits (153228)
#   api_key -> b5e40948-b398-41c2-9a8a-e9c003f4410f (UUID v1 or v4)

# returns:
#   .cdsapirc file
#   format:
'''
        url: https://cds.climate.copernicus.eu/api/v2
        key: 153228:b5e40948-b398-41c2-9a8a-e9c003f4410f
'''
# checks for connection
#   cdsapi.Client().status()
#   should return -> {'info': ['Welcome to the CDS'], 'warning': []}
#
# handles connection errors
help = 'Use `help(extract_grib)` for more info.'
help_con = 'Use `help(extract_grib.connection())` for more info.'
cdsapirc = Path.home() / '.cdsapirc'
credentials = 'url: https://cds.climate.copernicus.eu/api/v2\n' \
              'key: '

#
def interactive_con(answer):
    no = ['N','n','No','no','NO']
    if answer not in no:
        uid = str(input('Insert UID: '))
        key = str(input('Insert API Key: '))
        return uid, key
    else:
        logging.info('Usage: `extract_grib.connect(uid, key)`')

# Return credentials if valid
def check_credentials(uid, key):
    valid_uid = eval('len(uid) == 6')
    valid_key = eval('uuid.UUID(key).version == 4')
    if not valid_uid:
        return logging.error('Invalid UID. '+
                             f'{help_con}')
    if not valid_key:
        return logging.error('Invalid API Key. '+
                             f'{help_con}')
    return uid, key

# uid(optional) str
# key(optional) str
def connect(uid: Optional[str] = None,
            key: Optional[str] = None,
            ):

    if not uid and not key:
        try:
            # check for valid uid and key
            status = cdsapi.Client().status()
            logging.info('Credentials file configured.')
            logging.info(status['info'])
            logging.warning(status['warning'])

        except Exception as e:
            logging.error(e)

            # enter interactive mode
            answer = input('Enter interactive mode? (y/n): ')
            uid_answer, key_answer = interactive_con(answer)
            uid, key = check_credentials(uid_answer, key_answer)

            # store credentials
            with open(cdsapirc, 'w') as f:
                f.write(credentials + f'{uid}:{key}')
                logging.info(f'Credentials stored at {cdsapirc}')

        finally:
            return cdsapi.Client()

    try:
        uid, key = check_credentials(uid, key)
        with open(cdsapirc, 'w') as f:
            f.write(credentials + f'{uid}:{key}')
            logging.info(f'Credentials stored at {cdsapirc}')

        cdsapi.Client().status()
        return cdsapi.Client()

    except Exception as e:
        logging.error(e)


# con = cdsapi.Client()


# recebe:
#
#   data inicial -> 'YYYY-MM-DD'
#   data final (past) -> 'YYYY-MM-DD'
#   SE -> 'YYYY-SE' ?(medium)

# returns:
#   grib file
#   YYMMDD_YYMMDD.grib ? fix?

#   gotta check if client is set correctly
#   max range (1 month?)
#   choose which variable?
#   choose between 3h range or 1h range?
#   choose the coordinations to get? (difficult)

def download(ini: str,
             end: Optional[str] = None,
            #  epi_week: Optional[Union[list[str], str]] = None,
             filename: Optional[str] = None,
             uid: Optional[str] = None,
             key: Optional[str] = None
            ):

    conn = connect(uid, key)
    format = '%Y-%m-%d'
    iso_format = 'YYYY-MM-DD'
    re_format = r'\d{4}-\d{2}-\d{2}'
    today = datetime.now()
    ini_date = datetime.strptime(ini, format)

    # dataset has maximum of 7 days of update delay.
    # in order to prevent requesting invalid dates,
    # the max date is 7 days from today's date
    max_update_delay = today - timedelta(days=7)
    if ini_date > max_update_delay:
        return logging.error(f'''
                Invalid date. The last update date is:
                {datetime.strftime(max_update_delay, format)}
                {help}
        ''')

    # check for right initial date format
    if not re.match(re_format, ini):
        return logging.error(f'''
                Invalid initial date. Format:
                {iso_format}
                {help}
        ''')

    # an end date can be passed to define the date range
    # if there is no end date, only the day specified on
    # @param `ini` will be downloaded
    if end:
        # check for right end date format
        if not re.match(re_format, end):
            return logging.error(f'''
                    Invalid end date. Format:
                    {iso_format}
                    {help}
            ''')

        end_date = datetime.strptime(end, format)

        # example of file with date range:
        # 20210920_20220920.grib
        filename = f'{end}_{ini}.grib'

        # end date can't be bigger than initial date
        if end_date >= ini_date:
            return logging.error(f'''
                    Invalid date range.
                    {help}
            ''')

        df = pd.date_range(start=end, end=ini)






    conn.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'format': 'grib',
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
                5.27, -73.98, -33.75,
                -34.79,
            ],
        },
        f'data/{filename.replace("-","")}')


    # usage:
    #   extract_grib(date_range) -> grib file

    # if not .cdsapirc, use extract_grib.connect(UID, Key)
    # connect runs extract_grib.status() automatically, but can be ran manually too
