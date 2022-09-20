from typing import Optional, Union, Dict
import cdsapi
import uuid
import logging
from pathlib import Path
from datetime import datetime

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
                             f'{help}')
    if not valid_key:
        return logging.error('Invalid API Key. '+
                             f'{help}')
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

def download(year: Optional[str] = None,
             month: Optional[Union[list[str], str]] = None,
             day: Optional[Union[list[str], str]] = None,
            #  epi_week: Optional[Union[list[str], str]] = None,
             filename: Optional[str] = None,
             uid: Optional[str] = None,
             key: Optional[str] = None
            ):

    conn = connect(uid, key)
    today = datetime.now()
    date_format = '%Y-%m-%d'

    if len(day) == 1:
        day = f'{int(day):2d}'

    if len(month) == 1:
        month = f'{int(month):2d}'

    if not year:
        year = str(today.year)

    if int(year) == today.year and (not month and not day):
        day = []
        month = []

        if today.day <= 7:



    if not month and

    if day and not month:
        return logging.error(f'''
            Select at least one month.
            {help}
        ''')



    # # epi_week is only available with year
    # if epi_week and (month or day):
    #     return logging.error(f'''
    #         Unable to define the date range, please select
    #         only the epidemiological week(s) and/or the year.
    #         {help}
        ''')

    # # downloading the entire year is not possible
    # if year and not month or not day or not epi_week:
    #     return logging.error('''
    #         Range too long, please select the months or
    #         the epidemiological weeks.
    #     ''')


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
            'year': '2022',
            'month': '09',
            'day': '10',
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
        'data/test2.grib')


    # usage:
    #   extract_grib(date_range) -> grib file

    # if not .cdsapirc, use extract_grib.connect(UID, Key)
    # connect runs extract_grib.status() automatically, but can be ran manually too
