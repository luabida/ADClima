import logging
import cdsapi
from pathlib import Path
from typing import Optional


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
    """

    """
    no = ['N','n','No','no','NO']
    if answer not in no:
        uid = str(input('Insert UID: '))
        key = str(input('Insert API Key: '))
        return uid, key
    else:
        logging.info('Usage: `extract_grib.connect(uid, key)`')

# Return credentials if valid
def check_credentials(uid, key):
    """

    """
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
    """


    """

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
