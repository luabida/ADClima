import numpy as np

LONGITUDES = list(np.arange(-90.0,90.25,0.25))
LATITUDES = list(np.arange(-180.0,180.25,0.25))


def do_area(lat, lon) -> tuple:

    closest_lat = min(LATITUDES, key=lambda x: abs(x - lat))
    closest_lon = min(LONGITUDES, key=lambda x: abs(x - lon))

    first_quadr = lat - closest_lat < 0 and lon - closest_lon < 0
    second_quadr = lat - closest_lat > 0 and lon - closest_lon < 0
    third_quadr = lat - closest_lat > 0 and lon - closest_lon > 0
    fourth_quadr = lat - closest_lat < 0 and lon - closest_lon > 0

    if first_quadr:
        north, east = closest_lat, closest_lon
        i_south = [i - 1 for i, x in enumerate(LATITUDES) if x == north].pop()
        i_west = [i - 1 for i, y in enumerate(LONGITUDES) if y == east].pop()
        south, west = LATITUDES[i_south], LONGITUDES[i_west]

    if second_quadr:
        north, west = closest_lat, closest_lon
        i_south = [i - 1 for i, x in enumerate(LATITUDES) if x == north].pop()
        i_east = [i + 1 for i, y in enumerate(LONGITUDES) if y == west].pop()
        south, east = LATITUDES[i_south], LONGITUDES[i_east]

    if third_quadr:
        south, west = closest_lat, closest_lon
        i_north = [i + 1 for i, x in enumerate(LATITUDES) if x == south].pop()
        i_east = [i + 1 for i, y in enumerate(LONGITUDES) if y == west].pop()
        north, east = LATITUDES[i_north], LONGITUDES[i_east]

    if fourth_quadr:
        south, east = closest_lat, closest_lon
        i_north = [i - 1 for i, x in enumerate(LATITUDES) if x == south].pop()
        i_west = [i - 1 for i, y in enumerate(LONGITUDES) if y == east].pop()
        north, west = LATITUDES[i_north], LONGITUDES[i_west]

    return north, south, east, west
