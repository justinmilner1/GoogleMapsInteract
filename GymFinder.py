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
import os
from mpl_toolkits.basemap import Basemap
from geopy.distance import geodesic
import folium


# Configuration/Constants
API_KEY = open('secret.txt', 'r').read()
SEARCH_QUERY = 'jiu jitsu gym'
KEYWORDS = ['jiu-jitsu', 'jiu jitsu', 'bjj','mma', 'grappling', 'submission']
POPULATION_MIN = 140916
ORIGINAL_FILEPATH = 'jiu_jitsu_gyms.csv'
DEDUP_FILEPATH = 'dedup_jiu_jitsu_gyms.csv'
ZIP_CODE_COORDINATES_FILEPATH = 'zip_code_coordinates.json'
RADIUS_MODIFIER = 2.5
OVERLAP_THRESHOLD = 0.80
MAX_RADIUS = 15 * 1609.34 # miles to meters


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
        print("Got: " + zip_code)
        return center_lat, center_lng, northeast, southwest
    print("No results for zip code:", zip_code)
    print("response:", response.json().get('status'))
    return None, None, None, None

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

def form_places_query_url(location, radius):
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
    url = form_places_query_url(location, radius)

    while url:
        response = requests.get(url)
        data = response.json()


        #ToDo: Extract results properly

        gyms.extend(data.get('results', []))
        
        # Check for next page token
        next_page_token = data.get('next_page_token')
        if next_page_token:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?pagetoken={next_page_token}&key={API_KEY}"
            time.sleep(.75)  # To avoid hitting rate limits
        else:
            url = None
    
    return gyms

# Function to extract coordinates from the results and write to CSV
def extract_and_write_coordinates(results, writer):
    for place in results:
        name = place.get('name')
        lat = place['geometry']['location']['lat']
        lng = place['geometry']['location']['lng']
        #ToDo: I'd also like to write zipcode, city (any anything else that could be interesting)
        writer.writerow({'Name': name, 'Latitude': lat, 'Longitude': lng})

# Function to collect gyms for a given coordinate and write results to CSV
def collect_and_write_gyms(lat_lng, radius, city, writer):
    location = f"{lat_lng[0]},{lat_lng[1]}"
    gyms = find_gyms(location, radius)
    extract_and_write_coordinates(gyms, writer)

def make_google_places_requests(zip_codes_to_coordinates):
    with open(ORIGINAL_FILEPATH, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=KEYWORDS)
        
        writer.writeheader()
        
        # Collect gyms data and write to CSV without parallel processing
        for lat_lng, radius, city in zip_codes_to_coordinates:
            try:
                collect_and_write_gyms(lat_lng, radius, city, writer)
            except Exception as exc:
                print(f"An error occurred: {exc}")

def get_city_name_to_zip_codes():
    city_name_to_zip_codes = {}
    with open('uscities.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Filter us cities list for only cities with populations greater than 50,000
            if int(row['population']) < POPULATION_MIN and int(row['population']) > 50000: #should go til around Murray, UT ~#946
                zip_codes = row['zips'].split(' ')
                if row['city'] not in city_name_to_zip_codes:
                    city_name_to_zip_codes[row['city']] = zip_codes
                else:
                    city_name_to_zip_codes[row['city']].extend(zip_codes)
    return city_name_to_zip_codes

def visualize_coordinates_and_radiuses(city_name_to_zip_codes_coordinates, filename):
    # Create a folium map centered on the US
    m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)

    # Extract coordinates and radii for each city
    for zip_code in city_name_to_zip_codes_coordinates:
        (center_lat, center_lng), radius, city = city_name_to_zip_codes_coordinates[zip_code]

        # Add a circle to the map
        folium.Circle(
            location=(center_lat, center_lng),
            radius=radius,
            color='blue',
            fill=True,
            fill_opacity=0.3,
            popup=f"{city} ({zip_code})"
        ).add_to(m)

    # Save the map to an HTML file
    m.save(filename)

def get_city_name_to_zip_codes_coordinates(city_name_to_zip_codes):
    for city in city_name_to_zip_codes:
        zip_codes_to_coordinates = {} # zip_code_name -> [(lat, lng), radius, city]
        for zip_code in city_name_to_zip_codes[city]:
            center_lat, center_lng, northeast, southwest = get_zip_code_bounding_box(zip_code)
            if northeast and southwest:
                # Calculate an approximate radius based on viewport object
                radius = calculate_radius(northeast, southwest)
                zip_codes_to_coordinates[zip_code] = [(center_lat, center_lng), radius, city]
            else:
                print(f"Failed to get zip code info for {city}: {zip_code}")
            time.sleep(.75) # To avoid hitting rate limits

        # after each city, write to the document
        write_zip_code_coordinates(zip_codes_to_coordinates)
    return zip_codes_to_coordinates

def remove_duplicates():
    seen = set()
    unique_entries = []

    # Read the original file and collect unique entries
    with open(ORIGINAL_FILEPATH, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Create a unique identifier for each entry (e.g., a tuple of name, latitude, and longitude)
            identifier = (row['Zip_Code'], row['Latitude'], row['Longitude'])
            if identifier not in seen:
                seen.add(identifier)
                unique_entries.append(row)

    # Write the unique entries to the deduplicated file
    with open(DEDUP_FILEPATH, 'w', newline='') as csvfile:
        fieldnames = ['Zip_Code', 'Latitude', 'Longitude']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for entry in unique_entries:
            writer.writerow(entry)

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

def read_zip_code_coordinates():
    city_name_to_zip_codes_coordinates = {}
    with open(ZIP_CODE_COORDINATES_FILEPATH, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            zip_code = row['Zip_Code']
            city = row['City']
            lat = float(row['Latitude'])
            lng = float(row['Longitude'])
            radius = float(row['Radius'])
            city_name_to_zip_codes_coordinates[zip_code] = [(lat, lng), radius, city]
    return city_name_to_zip_codes_coordinates

def radius_modifier(zip_codes_to_coordinates):
    #iterate through zip_codes_to_coordinates and modify radius by RADIUS_MODIFIER
    for zip_code in zip_codes_to_coordinates:
        (lat, lng), radius, city = zip_codes_to_coordinates[zip_code]
        radius = radius * RADIUS_MODIFIER
        zip_codes_to_coordinates[zip_code] = [(lat, lng), radius, city]
    return zip_codes_to_coordinates

def calculate_distance(coord1, coord2):
    """Calculate the distance between two coordinates (latitude, longitude)."""
    lat1, lng1 = coord1
    lat2, lng2 = coord2
    # Haversine formula to calculate the distance between two points on the Earth
    R = 6371  # Radius of the Earth in kilometers
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def calculate_overlap_area(r1, r2, d):
    """Calculate the area of overlap between two circles with radii r1 and r2 and distance d between centers."""
    if d >= r1 + r2:
        return 0  # No overlap
    if d <= abs(r1 - r2):
        return math.pi * min(r1, r2) ** 2  # One circle is completely inside the other

    r1_sq = r1 ** 2
    r2_sq = r2 ** 2
    d_sq = d ** 2

    part1 = r1_sq * math.acos((d_sq + r1_sq - r2_sq) / (2 * d * r1))
    part2 = r2_sq * math.acos((d_sq + r2_sq - r1_sq) / (2 * d * r2))
    part3 = 0.5 * math.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))

    return part1 + part2 - part3

def remove_redundant_circles(zip_codes_to_coordinates):
    """
    Remove circles overlap by OVERLAP_THRESHOLD amount. (remove the smaller of the two circles)

    zip_codes_to_coordinates is a dictionary. zip_code -> (lat,lng), radius, city
    """
    num_removed = 0
    num_kept = 0
    filtered_coordinates = {}

    zip_codes_list = list(zip_codes_to_coordinates.items())

    for i, (zip_code1, ((lat1, lng1), radius1, city1)) in enumerate(zip_codes_list):
        is_redundant = False
        for j, (zip_code2, ((lat2, lng2), radius2, city2)) in enumerate(zip_codes_list):
            if i != j:
                distance_meters = calculate_distance((lat1, lng1), (lat2, lng2)) * 1000  # Convert to meters
                # Check if circle1 is fully enveloped by circle2
                if distance_meters + radius1 <= radius2:
                    is_redundant = True
                    break
        if not is_redundant:
            filtered_coordinates[zip_code1] = [(lat1, lng1), radius1, city1]
            num_kept += 1
        else:
            num_removed += 1

    print("Number of redundant circles removed: ", num_removed)
    print("Number of circles kept: ", num_kept)
    return filtered_coordinates

    

def remove_excessive_circles(zip_codes_to_coordinates):
    """Remove circles that have a radius greater than MAX_RADIUS."""
    num_removed = 0
    num_kept = 0
    filtered_coordinates = {}
    for zip_code in zip_codes_to_coordinates:
        (lat, lng), radius, city = zip_codes_to_coordinates[zip_code]
        if radius <= MAX_RADIUS:
            num_kept += 1
            filtered_coordinates[zip_code] = [(lat, lng), radius, city]
        else:
            num_removed += 1
    print("Number of excessive circles removed: ", num_removed)
    print("Number of circles kept: ", num_kept)
    return filtered_coordinates

#############################################################################################


#if not os.path.exists(ZIP_CODE_COORDINATES_FILEPATH):
print("Zip coordinates file not found, retrieving zip code coordinates. Press enter to continue")
input()

# Gather list of coordinates 
city_name_to_zip_codes = get_city_name_to_zip_codes()
print('Number of Cities: ', len(city_name_to_zip_codes))
print('Number of Zip Codes: ', sum([len(zip_codes) for zip_codes in city_name_to_zip_codes.values()]))

# Retrive coordinates and viewport object via google reverse geocoding api, calculate radii
zip_codes_to_coordinates = get_city_name_to_zip_codes_coordinates(city_name_to_zip_codes)

city_name_to_zip_codes = None # Deallocate memory where possible
print("Completed retrieving zip code coordinates")


print("Zip coordinates file exists. Next up, vizualization.")

# Reading in zip code coordinates and radiuses
zip_codes_to_coordinates = read_zip_code_coordinates()

# Modify radii size
zip_codes_to_coordinates = radius_modifier(zip_codes_to_coordinates)
visualize_coordinates_and_radiuses(zip_codes_to_coordinates, "map_after_radius_modification.html")

# Remove circles with excessively large radius
zip_codes_to_coordinates = remove_excessive_circles(zip_codes_to_coordinates)
visualize_coordinates_and_radiuses(zip_codes_to_coordinates, "map_after_excessive_circle_removal.html")


# remove redundant circles
zip_codes_to_coordinates = remove_redundant_circles(zip_codes_to_coordinates)
visualize_coordinates_and_radiuses(zip_codes_to_coordinates, "map_after_redundant_circle_removal.html")







print("Next up, google places api. Press Enter to continue...")
input() 

# Search each zip code coordinates + radius pair using google places api with keywords
make_google_places_requests(zip_codes_to_coordinates)
print("Data collection complete. Results saved to jiu_jitsu_gyms.csv")


# Make new file with duplicates removed
remove_duplicates()
print("Duplicates removed. Results saved to jiu_jitsu_gyms_dedup.csv")



