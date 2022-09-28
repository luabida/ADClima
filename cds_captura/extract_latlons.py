import pandas as pd
import json

mun_json = open('/home/luabida/Projetos/InfoDengue/ADClima/data/municipios.json')

mun_decoded = mun_json.read().encode().decode('utf-8-sig')

municipios = json.loads(mun_decoded)

mun_json.close()

def from_geocode(geocode: int) -> tuple:
    df = pd.DataFrame(municipios)
    df = df.set_index('geocodigo')

    lat = df.loc[geocode].latitude
    lon = df.loc[geocode].longitude
    return lat, lon

def from_city_name(name: str) -> tuple:
    name = name.lower()
    df = pd.DataFrame(municipios)
    df['municipio'] = df['municipio'].str.lower()
    df = df.set_index('municipio')

    lat = df.loc[name].latitude
    lon = df.loc[name].longitude
    geocode = df.loc[name].geocodigo
    return lat, lon, geocode
