import pandas as pd
import geopandas as gpd

# recebe geocodigo, retorna lat e lon

def lat_lon(geocodigo):
    br_df = gpd.read_file('data/BR_Localidades_2010_v1.dbf')
    df = pd.DataFrame(br_df)
