"""
Adds state and population info to zip code coordinates.

Input: data/initial_coordinates.csv
    - Zip_Code,Latitude,Longitude,Radius,City
Output: data/inital_coordinates2.csv
    - Zip_Code,Latitude,Longitude,Radius,City,State,Population




"""
import csv 
import os

INITIAL_COORDINATES_FILEPATH = 'data/initial_coordinates.csv'
INITIAL_COORDINATES_FILEPATH2 = 'data/initial_coordinates2.csv'

def read_zip_code_coordinates():
    city_name_to_zip_codes_coordinates = {}
    with open(INITIAL_COORDINATES_FILEPATH, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            zip_code = row['Zip_Code']
            city = row['City']
            lat = float(row['Latitude'])
            lng = float(row['Longitude'])
            radius = float(row['Radius'])
            city_name_to_zip_codes_coordinates[zip_code] = [(lat, lng), radius, city]
    return city_name_to_zip_codes_coordinates

def write_zip_code_coordinates(zip_codes_to_coordinates):
    file_exists = os.path.isfile(INITIAL_COORDINATES_FILEPATH2)

    with open(INITIAL_COORDINATES_FILEPATH2, 'a', newline='') as csvfile:
        fieldnames = ['Zip_Code', 'Latitude', 'Longitude', 'Radius', 'City', 'State', 'Population']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()

        for zip_code in zip_codes_to_coordinates:
            (lat, lng), radius, city, state, population = zip_codes_to_coordinates[zip_code]
            writer.writerow({'Zip_Code': zip_code, 'Latitude': lat, 'Longitude': lng,
                              'Radius': radius, 'City': city, 'State': '', 'Population': ''})

def add_state_info(zip_codes_to_coordinates):
    zip_to_state = {}

    # Read the uszips.csv file and create a mapping of zip code to state name
    with open('data/uszips.csv', 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            zip_code = row['zip']
            state_name = row['state_name']
            zip_to_state[zip_code] = state_name

    # Add state information to the zip_codes_to_coordinates dictionary
    for zip_code in zip_codes_to_coordinates:
        if zip_code in zip_to_state:
            state_name = zip_to_state[zip_code]
            (lat, lng), radius, city = zip_codes_to_coordinates[zip_code]
            zip_codes_to_coordinates[zip_code] = [(lat, lng), radius, city, state_name]

    return zip_codes_to_coordinates
    

def add_population_info(zip_codes_to_coordinates):
    zip_to_population = {}

    # Read the uszips.csv file and create a mapping of zip code to population
    with open('data/uszips.csv', 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            zip_code = row['zip']
            population = row['population']
            zip_to_population[zip_code] = population

    # Add population information to the zip_codes_to_coordinates dictionary
    for zip_code in zip_codes_to_coordinates:
        if zip_code in zip_to_population:
            population = zip_to_population[zip_code]
            (lat, lng), radius, city, state = zip_codes_to_coordinates[zip_code]
            zip_codes_to_coordinates[zip_code] = [(lat, lng), radius, city, state, population]

    return zip_codes_to_coordinates

###########################################################################################

zip_codes_to_coordinates = read_zip_code_coordinates()


# Add State into to entries
zip_codes_to_coordinates = add_state_info(zip_codes_to_coordinates)

# Add population info to entries
zip_codes_to_coordinates = add_population_info(zip_codes_to_coordinates)

# Write to file
write_zip_code_coordinates(zip_codes_to_coordinates)