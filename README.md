# Google Maps Interaction

Data science work for [this]() article


Creates a list and visualization of jiu jitsu gyms and their coordinates in the US.
- City/County info provided by: https://simplemaps.com/data/
- Uses google maps places api to gather gym coordinates
- Visualizes data 

### How to use:
Run each of the python files below in the following order.


1) get_search_area.py → initial_coordinates.csv

- Uses google geocoding api and uscities.csv to get the inital search area coordinates/info
- Output: Zip_Code,Latitude,Longitude,Radius,City

2) add_state_and_population_info.py →inital_coordinates2.csv

- Adds state and population info
    - because I forgot to include this earlier
- Output: Zip_Code,Latitude,Longitude,Radius,City,State,Population

3) adjust_search_area.py → finalized_coordinates.csv

- Removes redundant entries, modifies radii
    - This is just to save costs a bit
- Output: Zip_Code,Latitude,Longitude,Radius,City,State,Population

4) get_gyms.py → jiu_jitsu_gyms.csv

- Uses coordinates+radii in finalized coordinates to generate list of gyms and their coordinates
- Output: Zip_Code, city, state, gym_name, lat, lng, anything else

5) count_gyms_by_city.py → gyms_by_city.csv

- Aggregates the number of gyms by city-state pairs
- city, state, population, num_gyms

6) count_gyms_by_zip_code.py → gyms_by_zip_code.csv

- Aggregates the number of gyms by zip_code
- Retrieves zip code population from
- zip_code, population, num_gyms











### Choosing dataset size:

| Population Minimum | Number of Cities | Number of Zip Codes | Cost
|--------------------|------------------|---------------------| -------
| 150,000            | 438              | 7479                | $176.00
| 200,000            | 218              | 6197                | $150.00
| 300,000            | 132              | 5392                | $123.20
| 450,000            | 96               | 4650                | $110.00
| 600,000            | 77               | 4251                | $94.00
| 750,000            | 62               | 3806                | $85.00
| 1,000,000          | 49               | 3341                | $75.00



Google maps provides a $200 monthly credit - I will go with the 200k population minimum so there's a bit of wiggle room.