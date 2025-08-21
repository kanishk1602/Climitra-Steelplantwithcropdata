import pandas as pd
import requests
import time

# Set your Google Maps Geocoding API key here
GOOGLE_MAPS_API_KEY = 'AIzaSyAFhC_CyUWgBnPbM9RKgrQBVUwt9VfrrwA'

INPUT_FILE = 'coordinates_separated.xlsx'  # Use the cleaned coordinates file
OUTPUT_FILE = 'with_district_state.xlsx'

# Read the Excel file
df = pd.read_excel(INPUT_FILE)

# Find the clean latitude and longitude columns
lat_col = 'Clean_Lat_Lat,Long'
lon_col = 'Clean_Lon_Lat,Long'

def reverse_geocode(lat, lon):
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'latlng': f'{lat},{lon}',
        'key': GOOGLE_MAPS_API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'OK' and data['results']:
            address_components = data['results'][0]['address_components']
            district = ''
            state = ''
            for comp in address_components:
                if 'administrative_area_level_2' in comp['types']:
                    district = comp['long_name']
                if 'administrative_area_level_1' in comp['types']:
                    state = comp['long_name']
            return district, state
    except Exception as e:
        print(f"Error reverse geocoding {lat},{lon}: {e}")
    return '', ''

# Print first few rows to verify data
print("First few rows of coordinates:")
print(df[[lat_col, lon_col]].head())
print("\nStarting geocoding...")

df['District'] = ''
df['State'] = ''

for idx, row in df.iterrows():
    try:
        lat = row[lat_col]
        lon = row[lon_col]
        
        if pd.isna(lat) or pd.isna(lon):
            print(f"Skipping row {idx}: Missing coordinates")
            continue
            
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            print(f"Skipping row {idx}: Invalid coordinates range: {lat}, {lon}")
            continue
        
        district, state = reverse_geocode(lat, lon)
        df.at[idx, 'District'] = district
        df.at[idx, 'State'] = state
        print(f"Row {idx}: {lat}, {lon} => {district}, {state}")
    except Exception as e:
        print(f"Error processing row {idx}: {str(e)}")
    time.sleep(0.2)  # Be polite to the API

df.to_excel(OUTPUT_FILE, index=False)
print(f"\nDone! Results saved to {OUTPUT_FILE}")
