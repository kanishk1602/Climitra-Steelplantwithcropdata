import plotly.express as px
import pandas as pd
import math
import streamlit as st

# Function to generate circle coordinates
def circle_coords(lon, lat, radius_km, n_points=100):
    coords = []
    for i in range(n_points):
        angle = 2 * math.pi * i / n_points
        dx = radius_km * math.cos(angle)
        dy = radius_km * math.sin(angle)
        dlon = dx / (111.32 * math.cos(math.radians(lat)))
        dlat = dy / 111.32
        coords.append((lon + dlon, lat + dlat))
    return coords

# Define Lantana clusters
lantana_clusters = [
    {"Region": "Western Ghats (Nilgiri)", "Latitude": 11.5, "Longitude": 76.5, 
     "Area_km2": 5711, "Description": "Lantana coverage: 30.33%, projected to increase"},
    {"Region": "Vindhyan Highlands", "Latitude": 24.5, "Longitude": 82.5, 
     "Area_km2": 200, "Description": "61-100% cover, highest biomass density"},
    {"Region": "Rajaji & Shivalik Hills", "Latitude": 30.2, "Longitude": 78.0, 
     "Area_km2": 100, "Description": "9 dry streambed clusters for daily harvesting"},
    {"Region": "Upper Ganga Valley", "Latitude": 29.0, "Longitude": 78.0, 
     "Area_km2": 231, "Description": "94% in subtropical zone, ideal for collection hubs"},
    {"Region": "Mudumalai TR", "Latitude": 11.6, "Longitude": 76.5, 
     "Area_km2": 100, "Description": "150 road-side patches with 87% mapping accuracy"},
    {"Region": "Jharkhand (Chotanagpur)", "Latitude": 23.5, "Longitude": 85.0, 
     "Area_km2": 10000, "Description": "~10,000 km² invaded, projected 20-26% by 2050"},
    {"Region": "Nainital Forests", "Latitude": 29.4, "Longitude": 79.5, 
     "Area_km2": 50, "Description": "Chir Pine forests with 2× higher biomass yield"}
]

# Define Juliflora clusters
juliflora_clusters = [
    {"Region": "Thar Desert", "Latitude": 26.3, "Longitude": 73.0, 
     "Area_km2": 341, "Description": "Dense Prosopis zones ideal for commercial harvesting"},
    {"Region": "Kachchh", "Latitude": 23.5, "Longitude": 70.0, 
     "Area_km2": 971, "Description": "Increased from 679 km² (1977) to 971 km² (2011)"},
    {"Region": "Viralimalai", "Latitude": 10.58, "Longitude": 78.65, 
     "Area_km2": 10.83, "Description": "2.1% invasion density, 59% patches high NDVI"},
    {"Region": "Avudayarkovil", "Latitude": 10.1, "Longitude": 79.0, 
     "Area_km2": 6.98, "Description": "1.6% invasion density"},
    {"Region": "Rajasthan (Jodhpur/Pali/Sirohi)", "Latitude": 26.0, "Longitude": 73.0, 
     "Area_km2": 500, "Description": "High economic return via charcoal production"},
    {"Region": "Tamil Nadu (Southern Zone)", "Latitude": 9.4, "Longitude": 78.8, 
     "Area_km2": 300, "Description": "Up to 182 trees/ha in dense stands"}
]

# Main Streamlit app
st.title("🗺️ Biochar Cluster Map with Steel Plants")
st.markdown("### Visualizing invasive species clusters for biochar production")

# Load steel plant data
@st.cache_data
def load_steel_plants():
    # For demo, using sample data - replace with your actual Excel file
    sample_plants = [
        {"Plant Name": "Tata Steel Jamshedpur", "latitude": 22.7749, "longitude": 86.2020},
        {"Plant Name": "JSW Steel Dolvi", "latitude": 20.9056, "longitude": 72.9329},
        {"Plant Name": "SAIL Rourkela", "latitude": 22.2244, "longitude": 84.8640},
        {"Plant Name": "AM/NS India Hazira", "latitude": 21.1291, "longitude": 72.7411}
    ]
    return pd.DataFrame(sample_plants)

plants = load_steel_plants()

# Species selection
species = st.radio("Select Biomass Species:", ["None", "Lantana", "Juliflora"])

# Create base map with steel plants
fig = px.scatter_mapbox(
    plants,
    lat="latitude",
    lon="longitude",
    hover_name="Plant Name",
    hover_data={"latitude": False, "longitude": False},
    zoom=4,
    height=700,
    mapbox_style="carto-positron",
    color_discrete_sequence=["red"],
)

# Set map center to India
fig.update_layout(mapbox_center={"lat": 20.5937, "lon": 78.9629})

# Add clusters based on selection
if species != "None":
    clusters = lantana_clusters if species == "Lantana" else juliflora_clusters
    color = "green" if species == "Lantana" else "blue"
    
    for cluster in clusters:
        radius_km = math.sqrt(cluster["Area_km2"] / math.pi)
        circle = circle_coords(cluster["Longitude"], cluster["Latitude"], radius_km)
        lons, lats = zip(*circle)
        
        # Add polygon
        fig.add_trace(px.line_mapbox(
            lat=list(lats) + [lats[0]],
            lon=list(lons) + [lons[0]],
            color_discrete_sequence=[f"rgba(0,{128 if color=='green' else 0},{0 if color=='green' else 128},0.3)"]
        ).data[0])
        
        # Add center marker
        fig.add_scattermapbox(
            lat=[cluster["Latitude"]],
            lon=[cluster["Longitude"]],
            mode="markers",
            marker=dict(size=10, color=color),
            name=cluster["Region"],
            hoverinfo="text",
            hovertext=f"{cluster['Region']}<br>{cluster['Description']}<br>Area: {cluster['Area_km2']} km²"
        )

# Add legend
fig.add_scattermapbox(
    lat=[None],
    lon=[None],
    mode="markers",
    marker=dict(size=10, color="red"),
    name="Steel Plants",
    hoverinfo="none"
)

st.plotly_chart(fig, use_container_width=True)

# Show cluster details
if species != "None":
    st.subheader(f"{species} Cluster Details")
    cluster_df = pd.DataFrame(lantana_clusters if species == "Lantana" else juliflora_clusters)
    st.dataframe(cluster_df[["Region", "Area_km2", "Description"]], 
                hide_index=True, 
                column_config={
                    "Region": "Region",
                    "Area_km2": st.column_config.NumberColumn("Area (km²)", format="%d km²"),
                    "Description": "Description"
                })
