'''
Removes redundant entries, modifies radii
    - This is just to save costs a bit

Output: finalized_coordinates.csv
     Zip_Code,Latitude,Longitude,Radius,City,State,Population

'''


import csv
import math
import folium
import os

# Configuration/Constants
API_KEY = open('secret.txt', 'r').read()
SEARCH_QUERY = 'jiu jitsu gym'
KEYWORDS = ['jiu-jitsu', 'jiu jitsu', 'bjj','mma', 'grappling', 'submission']
POPULATION_MIN = 140916
ORIGINAL_FILEPATH = 'data/jiu_jitsu_gyms.csv'
DEDUP_FILEPATH = 'data/dedup_jiu_jitsu_gyms.csv'
FINALIZED_COORDINATES_FILEPATH = 'data/finalized_coordinates.csv'
ZIP_CODE_COORDINATES_FILEPATH = 'data/zip_code_coordinates2.csv'
RADIUS_MODIFIER = 2.5
OVERLAP_THRESHOLD = 0.80
MAX_RADIUS = 15 * 1609.34 # miles to meters

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
            state = row['State']
            population = float(row['Population'])
            city_name_to_zip_codes_coordinates[zip_code] = [(lat, lng), radius, city, state, population]
    return city_name_to_zip_codes_coordinates

def radius_modifier(zip_codes_to_coordinates):
    #iterate through zip_codes_to_coordinates and modify radius by RADIUS_MODIFIER
    for zip_code in zip_codes_to_coordinates:
        (lat, lng), radius, city, state, population = zip_codes_to_coordinates[zip_code]
        radius = radius * RADIUS_MODIFIER
        zip_codes_to_coordinates[zip_code] = [(lat, lng), radius, city, state, population]
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

    for i, (zip_code1, ((lat1, lng1), radius1, city1, state1, population1)) in enumerate(zip_codes_list):
        is_redundant = False
        for j, (zip_code2, ((lat2, lng2), radius2, city2, state2, population2)) in enumerate(zip_codes_list):
            if i != j:
                distance_meters = calculate_distance((lat1, lng1), (lat2, lng2)) * 1000  # Convert to meters
                # Check if circle1 is fully enveloped by circle2
                if distance_meters + radius1 <= radius2:
                    is_redundant = True
                    break
        if not is_redundant:
            filtered_coordinates[zip_code1] = [(lat1, lng1), radius1, city1, state1, population1]
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
        (lat, lng), radius, city, state, population = zip_codes_to_coordinates[zip_code]
        if radius <= MAX_RADIUS:
            num_kept += 1
            filtered_coordinates[zip_code] = [(lat, lng), radius, city, state, population]
        else:
            num_removed += 1
    print("Number of excessive circles removed: ", num_removed)
    print("Number of circles kept: ", num_kept)
    return filtered_coordinates

def visualize_coordinates_and_radiuses(city_name_to_zip_codes_coordinates, filename):
    # Create a folium map centered on the US
    m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)

    # Extract coordinates and radii for each city
    for zip_code in city_name_to_zip_codes_coordinates:
        (center_lat, center_lng), radius, city, state, population = city_name_to_zip_codes_coordinates[zip_code]

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


def write_zip_code_coordinates(zip_codes_to_coordinates):
    file_exists = os.path.isfile(FINALIZED_COORDINATES_FILEPATH)

    with open(FINALIZED_COORDINATES_FILEPATH, 'a', newline='') as csvfile:
        fieldnames = ['Zip_Code', 'Latitude', 'Longitude', 'Radius', 'City', 'State', 'Population']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()

        for zip_code in zip_codes_to_coordinates:
            (lat, lng), radius, city, state, population = zip_codes_to_coordinates[zip_code]
            writer.writerow({'Zip_Code': zip_code, 'Latitude': lat, 'Longitude': lng, 'Radius': radius, 
                             'City': city, 'State': state, 'Population': population})




# Reading in zip code coordinates and radiuses
zip_codes_to_coordinates = read_zip_code_coordinates()

# Modify radii size
zip_codes_to_coordinates = radius_modifier(zip_codes_to_coordinates)
visualize_coordinates_and_radiuses(zip_codes_to_coordinates, "visualizations/map_after_radius_modification.html")

# Remove circles with excessively large radius
zip_codes_to_coordinates = remove_excessive_circles(zip_codes_to_coordinates)
visualize_coordinates_and_radiuses(zip_codes_to_coordinates, "visualizations/map_after_excessive_circle_removal.html")


# remove redundant circles
zip_codes_to_coordinates = remove_redundant_circles(zip_codes_to_coordinates)
visualize_coordinates_and_radiuses(zip_codes_to_coordinates, "visualizations/map_after_redundant_circle_removal.html")

#Save zip_codes_to_coordinates to finalized_coordinates.csv
write_zip_code_coordinates(zip_codes_to_coordinates)