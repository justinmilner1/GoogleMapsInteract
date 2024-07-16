###################################################################################
# *** Jiu Jitsu Gym Finder ***
# 
# 1) Gather list of coordinates and radiuses to perform search on
#  - Filter us cities list for only cities with populations greater than 50,000
#  - Retrive coordinates and viewport object via google reverse geocoding api
#  - Calculate an approximate radius based on viewport object
#
# 2) Gather list of jiu jitsu gym names and coordinates
#  - Search each zip code coordinates + radius pair using google places api with keywords
#
###################################################################################

import requests
import time
import csv
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import geopandas as gpd

# Configuration
API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY'

# Constants
SEARCH_QUERY = 'jiu jitsu gym'
KEYWORDS = ['jiu-jitsu', 'jiu jitsu', 'bjj','mma']
POPULATION_MIN = 200000
ORIGINAL_FILEPATH = 'jiu_jitsu_gyms.csv'
DEDUP_FILEPATH = 'dedup_jiu_jitsu_gyms.csv'


def get_zip_code_bounding_box(zip_code):
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={zip_code}&key={API_KEY}"
    response = requests.get(geocode_url)
    results = response.json().get('results')
    if results:
        viewport = results[0]['geometry']['viewport']
        northeast = viewport['northeast']
        southwest = viewport['southwest']
        center_lat = results[0]['geometry']['location']['lat']
        center_lng = results[0]['geometry']['location']['lng']
        return center_lat, center_lng, northeast, southwest
    return None, None

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

# Generate grid coordinates
def generate_grid_coordinates(min_lat, max_lat, min_lng, max_lng, step_lat, step_lng):
    coordinates = []
    lat = min_lat
    while lat <= max_lat:
        lng = min_lng
        while lng <= max_lng:
            coordinates.append((lat, lng))
            lng += step_lng
        lat += step_lat
    return coordinates


def form_query_url(location, radius):
    #unpack keywords
    keywords = '|'.join(KEYWORDS)

    #form query
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    query = f"jiu+jitsu+gym+({keywords})"
    url = f"{base_url}?query={query}&location={location}&radius={radius}&key={API_KEY}"
    return url

# Function to find gyms using the Google Places API
def find_gyms(location, radius):
    gyms = []

  # Form the query URL
    url = form_query_url(location, radius)

    while url:
        response = requests.get(url)
        data = response.json()
        gyms.extend(data.get('results', []))
        
        # Check for next page token
        next_page_token = data.get('next_page_token')
        if next_page_token:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?pagetoken={next_page_token}&key={API_KEY}"
            time.sleep(2)  # To avoid hitting rate limits
        else:
            url = None
    
    return gyms

# Function to extract coordinates from the results and write to CSV
def extract_and_write_coordinates(results, writer):
    for place in results:
        name = place.get('name')
        lat = place['geometry']['location']['lat']
        lng = place['geometry']['location']['lng']
        writer.writerow({'Name': name, 'Latitude': lat, 'Longitude': lng})

# Function to collect gyms for a given coordinate and write results to CSV
def collect_and_write_gyms(coord, writer):
    location = f"{coord[0]},{coord[1]}"
    gyms = find_gyms(location, radius)
    extract_and_write_coordinates(gyms, writer)

# Function to extract coordinates from the results and write to CSV
def extract_and_write_coordinates(results, writer):
    for place in results:
        name = place.get('name')
        lat = place['geometry']['location']['lat']
        lng = place['geometry']['location']['lng']
        writer.writerow({'Name': name, 'Latitude': lat, 'Longitude': lng})

# Function to collect gyms for a given coordinate and write results to CSV
def collect_and_write_gyms(lat_lng, radius, writer):
    location = f"{lat_lng[0]},{lat_lng[1]}"
    gyms = find_gyms(location, radius, search_query)
    extract_and_write_coordinates(gyms, writer)


def get_city_name_to_zip_codes():
    city_name_to_zip_codes = {}
    with open('uscities.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Filter us cities list for only cities with populations greater than 50,000
            if int(row['population']) >= POPULATION_MIN:
                zip_codes = row['zips'].split(' ')
                city_name_to_zip_codes[row['city']] = zip_codes
    return city_name_to_zip_codes

# def visualize_zip_codes(city_name_to_zip_codes):
#     fig, ax = plt.subplots(figsize=(10, 10))

#     for city, zip_codes in city_name_to_zip_codes.items():
#         for zip_code in zip_codes:
#             center_lat, center_lng, northeast, southwest = get_zip_code_bounding_box(zip_code)
#             if northeast and southwest:
#                 # Create a rectangle patch for the bounding box
#                 width = northeast['lng'] - southwest['lng']
#                 height = northeast['lat'] - southwest['lat']
#                 rect = patches.Rectangle((southwest['lng'], southwest['lat']), width, height, linewidth=1, edgecolor='blue', facecolor='none')
#                 ax.add_patch(rect)

#     plt.title('Zip Code Bounding Boxes')
#     plt.xlabel('Longitude')
#     plt.ylabel('Latitude')
#     plt.grid(True)
#     plt.show()

def visualize_coordinates_and_radiuses(city_name_to_zip_codes_coordinates):
    fig, ax = plt.subplots(figsize=(10, 6))

    # Extract coordinates and radii for each city
    for city, (center, radius) in city_name_to_zip_codes_coordinates.items():
        center_lat, center_lng = center
        # Convert radius from meters to degrees (approximation)
        radius_in_degrees = radius / 111320  # 1 degree is approximately 111.32 km or 111320 meters

        # Plot the center point
        ax.scatter(center_lng, center_lat, c='blue', marker='o', alpha=0.5)

        # Plot the radius as a circle
        circle = patches.Circle((center_lng, center_lat), radius_in_degrees, color='blue', fill=False, alpha=0.3)
        ax.add_patch(circle)

    # Set plot title and labels
    ax.set_title('Center Points and Radii of Zip Codes')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.grid(True)
    plt.show()


def get_city_name_to_zip_codes_coordinates(city_name_to_zip_codes):
    city_name_to_zip_codes_coordinates = {} # Name -> [(lat, lng), radius]
    for city in city_name_to_zip_codes:
        for zip_code in city_name_to_zip_codes[city]:
            center_lat, center_lng, northeast, southwest = get_zip_code_bounding_box(zip_code)
            if northeast and southwest:
                # Calculate an approximate radius based on viewport object
                radius = calculate_radius(northeast, southwest)
                city_name_to_zip_codes_coordinates[city] = [(center_lat, center_lng), radius]
            else:
                print(f"Invalid zip code for {city}: {zip_code}")
    return city_name_to_zip_codes_coordinates

def make_google_places_requests():
    with open(ORIGINAL_FILEPATH, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=KEYWORDS)
        
        writer.writeheader()
        
        # Collect gyms data and write to CSV without parallel processing
        for lat_lng, radius in city_name_to_zip_codes_coordinates:
            try:
                collect_and_write_gyms(lat_lng, radius, writer)
            except Exception as exc:
                print(f"An error occurred: {exc}")



def remove_duplicates():
    seen = set()
    unique_entries = []

    # Read the original file and collect unique entries
    with open(ORIGINAL_FILEPATH, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Create a unique identifier for each entry (e.g., a tuple of name, latitude, and longitude)
            identifier = (row['Name'], row['Latitude'], row['Longitude'])
            if identifier not in seen:
                seen.add(identifier)
                unique_entries.append(row)

    # Write the unique entries to the deduplicated file
    with open(DEDUP_FILEPATH, 'w', newline='') as csvfile:
        fieldnames = ['Name', 'Latitude', 'Longitude']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for entry in unique_entries:
            writer.writerow(entry)


#############################################################################################


# Gather list of coordinates and radiuses to perform search on
city_name_to_zip_codes = get_city_name_to_zip_codes()
print('Number of Cities: ', len(city_name_to_zip_codes))
print('Number of Zip Codes: ', sum([len(zip_codes) for zip_codes in city_name_to_zip_codes.values()]))

# Visualize the zip codes in the list
# visualize_zip_codes(city_name_to_zip_codes)
# print("Press Enter to continue...")
# input()

# Retrive coordinates and viewport object via google reverse geocoding api
city_name_to_zip_codes_coordinates = get_city_name_to_zip_codes_coordinates(city_name_to_zip_codes)
# Deallocate memory where possible
city_name_to_zip_codes = None

# Visualize coordinates and radiuses
visualize_coordinates_and_radiuses(city_name_to_zip_codes_coordinates)
print("Press Enter to continue...")
input() 

# Search each zip code coordinates + radius pair using google places api with keywords
make_google_places_requests(city_name_to_zip_codes_coordinates)
print("Data collection complete. Results saved to jiu_jitsu_gyms.csv")


# Make new file with duplicates removed
remove_duplicates()



