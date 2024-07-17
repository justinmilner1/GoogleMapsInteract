import requests
import time
import csv
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
from mpl_toolkits.basemap import Basemap
from geopy.distance import geodesic
import folium


# Configuration/Constants
API_KEY = open('secret.txt', 'r').read()
SEARCH_QUERY = 'jiu jitsu gym'
KEYWORDS = ['jiu-jitsu', 'jiu jitsu', 'bjj','mma', 'grappling', 'submission']
POPULATION_MIN = 50000
ORIGINAL_FILEPATH = 'data/jiu_jitsu_gyms.csv'
DEDUP_FILEPATH = 'data/dedup_jiu_jitsu_gyms.csv'
ZIP_CODE_COORDINATES_FILEPATH = 'data/zip_code_coordinates.csv'
RADIUS_MODIFIER = 2.5
OVERLAP_THRESHOLD = 0.80
MAX_RADIUS = 15 * 1609.34 # miles to meters

def calculate_radius(northeast, southwest):
    # Calculate the center point
    center_lat = (northeast['lat'] + southwest['lat']) / 2
    center_lng = (northeast['lng'] + southwest['lng']) / 2

    # Calculate the radius using the Haversine formula
    R = 6371000  # Earth radius in meters

    lat1 = math.radians(center_lat)
    lon1 = math.radians(center_lng)
    lat2 = math.radians(northeast['lat'])
    lon2 = math.radians(northeast['lng'])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    radius = R * c
    return radius

def get_city_name_to_zip_codes():
    city_name_to_zip_codes = {}
    with open('data/uscities.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Filter us cities list for only cities with populations greater than 50,000
            if int(row['population']) >= POPULATION_MIN: 
                zip_codes = row['zips'].split(' ')
                if row['city'] not in city_name_to_zip_codes:
                    city_name_to_zip_codes[row['city']] = zip_codes
                else:
                    city_name_to_zip_codes[row['city']].extend(zip_codes)
    return city_name_to_zip_codes

def write_zip_code_coordinates(zip_codes_to_coordinates):
    file_exists = os.path.isfile(ZIP_CODE_COORDINATES_FILEPATH)

    with open(ZIP_CODE_COORDINATES_FILEPATH, 'a', newline='') as csvfile:
        fieldnames = ['Zip_Code', 'Latitude', 'Longitude', 'Radius', 'City']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()

        for zip_code in zip_codes_to_coordinates:
            (lat, lng), radius, city = zip_codes_to_coordinates[zip_code]
            writer.writerow({'Zip_Code': zip_code, 'Latitude': lat, 'Longitude': lng, 'Radius': radius, 'City': city})


# Gather list of coordinates 
city_name_to_zip_codes = get_city_name_to_zip_codes()
print('Number of Cities: ', len(city_name_to_zip_codes))
print('Number of Zip Codes: ', sum([len(zip_codes) for zip_codes in city_name_to_zip_codes.values()]))