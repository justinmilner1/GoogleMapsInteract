import requests
import time
import concurrent.futures
import csv

# Configuration
API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY'
search_query = 'jiu jitsu gym'
radius = 50000  # 50 km radius
center_lat, center_lng = 39.8283, -98.5795  # Center of the contiguous US
step_lat, step_lng = 1, 1  # 1 degree steps (adjust based on desired granularity)
num_steps = 20  # Adjust based on desired coverage

# Generate grid coordinates
def generate_grid_coordinates(center_lat, center_lng, step_lat, step_lng, num_steps):
    coordinates = []
    for i in range(-num_steps, num_steps + 1):
        for j in range(-num_steps, num_steps + 1):
            coordinates.append((center_lat + i * step_lat, center_lng + j * step_lng))
    return coordinates

grid_coordinates = generate_grid_coordinates(center_lat, center_lng, step_lat, step_lng, num_steps)

# Function to find gyms using the Google Places API
def find_gyms(location, radius, search_query, api_key):
    gyms = []
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&keyword={search_query}&key={api_key}"
    
    while url:
        response = requests.get(url)
        data = response.json()
        gyms.extend(data.get('results', []))
        
        # Check for next page token
        next_page_token = data.get('next_page_token')
        if next_page_token:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?pagetoken={next_page_token}&key={api_key}"
            time.sleep(2)  # To avoid hitting rate limits
        else:
            url = None
    
    return gyms

# Function to extract coordinates from the results
def extract_coordinates(results):
    gyms = []
    for place in results:
        name = place.get('name')
        lat = place['geometry']['location']['lat']
        lng = place['geometry']['location']['lng']
        gyms.append((name, lat, lng))
    return gyms

# Function to collect gyms for a given coordinate
def collect_gyms(coord):
    location = f"{coord[0]},{coord[1]}"
    return find_gyms(location, radius, search_query, API_KEY)

# Use parallel processing to collect gyms data
all_gyms_us = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    future_to_coord = {executor.submit(collect_gyms, coord): coord for coord in grid_coordinates}
    for future in concurrent.futures.as_completed(future_to_coord):
        try:
            gyms = future.result()
            all_gyms_us.extend(gyms)
        except Exception as exc:
            print(f"An error occurred: {exc}")

# Extract coordinates
us_coordinates = extract_coordinates(all_gyms_us)

# Save results to a CSV file
with open('jiu_jitsu_gyms.csv', 'w', newline='') as csvfile:
    fieldnames = ['Name', 'Latitude', 'Longitude']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    for gym in us_coordinates:
        writer.writerow({'Name': gym[0], 'Latitude': gym[1], 'Longitude': gym[2]})

print("Data collection complete. Results saved to jiu_jitsu_gyms.csv")
