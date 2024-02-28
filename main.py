# Importing required libraries
import pandas as pd
import geopandas as gpd
import numpy as np
import webbrowser as wb
import folium
from pyproj import CRS
from shapely.geometry import Point
from geopy.distance import geodesic


# Loading and formatting dataset
df_FFR = pd.read_csv('reference_data/FastFoodRestaurants.csv')
df_FFR = df_FFR[['name', 'address', 'city', 'province', 'latitude', 'longitude']]
df_FFR.rename(columns={'province':'state'}, inplace=True)


# Creating data subsets
# Mcdonalds in NY
df_MD_NY = df_FFR.loc[(df_FFR.state=='NY')&(df_FFR.name.isin(['McDonald\'s', 'McDonalds', 'Mcdonald\'s']))]
df_MD_NY.reset_index(drop=True, inplace=True)
# Burger Kings in NY
df_BK_NY = df_FFR.loc[(df_FFR.state=='NY')&(df_FFR.name.isin(['Burger King']))]
df_BK_NY.reset_index(drop=True, inplace=True)

# print(df_MD_NY.iloc[0])


# Function to combine latitude, longitue to a single point
# Returns original dataframe with point geometry as a column
def create_point (df, Long, Lat):
    crs = CRS('epsg:4326')
    geometry = [Point(xy) for xy in zip(df[Long], df[Lat])]
    df = gpd.GeoDataFrame(df, geometry=geometry).set_crs(crs, allow_override=True)
    df.rename(columns={'geometry':'Centroid'}, inplace=True)
    return df

df_MD_NY = create_point(df_MD_NY, 'longitude', 'latitude')
df_BK_NY = create_point(df_BK_NY, 'longitude', 'latitude')

# print(df_MD_NY.iloc[0])


# Takes a list of radii to create a buffer area around the points in a dataframe
def create_buffer_area (df, geometry_col, radius_list):
    gdf = gpd.GeoDataFrame(df, geometry=geometry_col)
    gdf.to_crs(epsg=2272, inplace=True)
    rdf = gpd.GeoDataFrame()
    for r in radius_list:
        tadf = pd.merge(
            df,
            gpd.GeoDataFrame(gdf.geometry.buffer(r*5280)),
            left_index=True,
            right_index=True
        )
        tadf['Radius'], tadf['Radius_Type'] = r, 'Mile'
        rdf = pd.concat([rdf, tadf])
    rdf.rename(columns={0: 'Buffer_Area'}, inplace=True)
    rdf = gpd.GeoDataFrame(rdf, geometry=geometry_col)
    rdf.to_crs(epsg=4326, inplace=True)
    return rdf

# list of trade area radius
radii = [3]
df_MD_NY = create_buffer_area(df_MD_NY, 'Centroid', radii)

# print(df_MD_NY.iloc[0])


# Plots the latitude, longitude and trade area from a dataframe to a map
def plot_point_polygon (df, latitude, longitude, trade_area):
    # Create base map and center the map
    middle_long = np.median(df[longitude])
    middle_lat = np.median(df[latitude])
    m = folium.Map(location=[middle_lat, middle_long], width='100%', height='100%', tiles='OpenStreetMap', zoom_start=7)
    # Plot latitude and longitude
    for idx, r in df.iterrows():
        folium.Marker([r[latitude], r[longitude]]).add_to(m)
    polys = df[trade_area]
    # Plot trade area as polygons
    folium.GeoJson(polys.to_crs(epsg=4326)).add_to(m)
    return m

ffr_map = plot_point_polygon(df_MD_NY, 'latitude', 'longitude', 'Buffer_Area')
ffr_map.save('map.html')
wb.open('map.html')