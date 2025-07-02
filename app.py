import plotly.express as px
import pandas as pd
import math
import streamlit as st
import json
import os

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
    {"Region": "Western Ghats (Nilgiri)", "Latitude": 11.5, "Longitude": 76.5, "Area_km2": 5711, "Description": "Lantana coverage: 30.33%, projected to increase"},
    {"Region": "Vindhyan Highlands", "Latitude": 24.5, "Longitude": 82.5, "Area_km2": 200, "Description": "61-100% cover, highest biomass density"},
    {"Region": "Rajaji & Shivalik Hills", "Latitude": 30.2, "Longitude": 78.0, "Area_km2": 100, "Description": "9 dry streambed clusters for daily harvesting"},
    {"Region": "Upper Ganga Valley", "Latitude": 29.0, "Longitude": 78.0, "Area_km2": 231, "Description": "94% in subtropical zone, ideal for collection hubs"},
    {"Region": "Mudumalai TR", "Latitude": 11.6, "Longitude": 76.5, "Area_km2": 100, "Description": "150 road-side patches with 87% mapping accuracy"},
    {"Region": "Jharkhand (Chotanagpur)", "Latitude": 23.5, "Longitude": 85.0, "Area_km2": 10000, "Description": "~10,000 km² invaded, projected 20-26% by 2050"},
    {"Region": "Nainital Forests", "Latitude": 29.4, "Longitude": 79.5, "Area_km2": 50, "Description": "Chir Pine forests with 2× higher biomass yield"}
]

# Define Juliflora clusters
juliflora_clusters = [
    {"Region": "Thar Desert", "Latitude": 26.3, "Longitude": 73.0, "Area_km2": 341, "Description": "Dense Prosopis zones ideal for commercial harvesting"},
    {"Region": "Kachchh", "Latitude": 23.5, "Longitude": 70.0, "Area_km2": 971, "Description": "Increased from 679 km² (1977) to 971 km² (2011)"},
    {"Region": "Viralimalai", "Latitude": 10.58, "Longitude": 78.65, "Area_km2": 10.83, "Description": "2.1% invasion density, 59% patches high NDVI"},
    {"Region": "Avudayarkovil", "Latitude": 10.1, "Longitude": 79.0, "Area_km2": 6.98, "Description": "1.6% invasion density"},
    {"Region": "Rajasthan (Jodhpur/Pali/Sirohi)", "Latitude": 26.0, "Longitude": 73.0, "Area_km2": 500, "Description": "High economic return via charcoal production"},
    {"Region": "Tamil Nadu (Southern Zone)", "Latitude": 9.4, "Longitude": 78.8, "Area_km2": 300, "Description": "Up to 182 trees/ha in dense stands"}
]

# Main Streamlit app
st.title("🗺️ Biochar Cluster Map with Steel Plants and GeoJSON Overlays")
st.markdown("### Visualizing invasive species clusters and steel plants")

# Load steel plant data
@st.cache_data
def load_steel_plants():
    try:
        df = pd.read_excel("plants_with_filled_data.xlsx")
        if not all(col in df.columns for col in ["Plant Name", "latitude", "longitude"]):
            st.error("Excel file is missing required columns: 'Plant Name', 'latitude', 'longitude'")
            return pd.DataFrame(columns=["Plant Name", "latitude", "longitude"])
        df = df.dropna(subset=["latitude", "longitude"])
        return df[["Plant Name", "latitude", "longitude"]]
    except Exception as e:
        st.error(f"Error loading steel plants data: {str(e)}")
        return pd.DataFrame(columns=["Plant Name", "latitude", "longitude"])

plants = load_steel_plants()

with st.expander("Data Debug Info"):
    st.write(f"Loaded {len(plants)} steel plants")
    st.dataframe(plants)
    invalid_coords = plants[(plants["latitude"].abs() > 90) | (plants["longitude"].abs() > 180)]
    if not invalid_coords.empty:
        st.warning(f"Found {len(invalid_coords)} plants with invalid coordinates:")
        st.dataframe(invalid_coords)

species = st.radio("Select Biomass Species:", ["None", "Lantana", "Juliflora"])
geojson_file = st.selectbox("Select GeoJSON Overlay:", ["None","lantanapresence.geojson","juliflora.geojson","cottonstalk.geojson","sugarcane.geojson"])

if not plants.empty:
    # Create base map with steel plants in purple
    fig = px.scatter_mapbox(
        plants,
        lat="latitude",
        lon="longitude",
        hover_name="Plant Name",
        zoom=4,
        height=800,
        mapbox_style="carto-positron",
        color_discrete_sequence=["purple"],  # Changed steel plants to purple
        title="Steel Plants"
    )
    fig.update_layout(mapbox_center={"lat": 20.5937, "lon": 78.9629}, margin={"r":0,"t":0,"l":0,"b":0})

    if species != "None":
        clusters = lantana_clusters if species == "Lantana" else juliflora_clusters
        color = "green" if species == "Lantana" else "blue"
        for cluster in clusters:
            radius_km = math.sqrt(cluster["Area_km2"] / math.pi)
            circle = circle_coords(cluster["Longitude"], cluster["Latitude"], radius_km)
            lons, lats = zip(*circle)
            fig.add_trace(px.line_mapbox(lat=list(lats) + [lats[0]], lon=list(lons) + [lons[0]], color_discrete_sequence=[f"rgba(0,{128 if color=='green' else 0},{0 if color=='green' else 128},0.3)"]).data[0])
            fig.add_scattermapbox(lat=[cluster["Latitude"]], lon=[cluster["Longitude"]], mode="markers+text", marker=dict(size=10, color=color), name=cluster["Region"], hoverinfo="text", hovertext=f"{cluster['Region']}<br>{cluster['Description']}<br>Area: {cluster['Area_km2']} km²", text=cluster["Region"], textposition="bottom center")

    # Add GeoJSON overlay if selected - using orange color
    if geojson_file != "None" and os.path.exists(geojson_file):
        with open(geojson_file) as f:
            geojson_data = json.load(f)
        for feature in geojson_data["features"]:
            geom_type = feature["geometry"]["type"]
            coords = feature["geometry"]["coordinates"]

            if geom_type == "Polygon" and coords and coords[0]:
                try:
                    lons, lats = zip(*coords[0])  # outer ring
                    fig.add_trace(
                        px.line_mapbox(
                            lat=list(lats) + [lats[0]],
                            lon=list(lons) + [lons[0]],
                            color_discrete_sequence=["rgba(255, 165, 0, 0.5)"]
                        ).data[0]
                    )
                except Exception as e:
                    st.warning(f"⚠️ Skipped a polygon due to error: {e}")
            elif geom_type == "Point":
                lon, lat = coords
                fig.add_scattermapbox(
                lat=[lat],
                lon=[lon],
                mode="markers",
                marker=dict(size=8, color="orange"),
                name="GeoJSON Point",
                hovertext=json.dumps(feature["properties"]),
                hoverinfo="text"
            )
            elif geom_type == "MultiPolygon":
                try:
                    for polygon in coords:
                        if polygon and polygon[0]:
                            lons, lats = zip(*polygon[0])
                            fig.add_trace(
                                px.line_mapbox(
                                    lat=list(lats) + [lats[0]],
                                    lon=list(lons) + [lons[0]],
                                    color_discrete_sequence=["rgba(255, 165, 0, 0.5)"]
                                ).data[0]
                            )
                except Exception as e:
                    st.warning(f"⚠️ Skipped a MultiPolygon due to error: {e}")


    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No steel plant data available. Please check your Excel file.")

if species != "None" and plants.empty:
    st.subheader(f"{species} Cluster Details")
    cluster_df = pd.DataFrame(lantana_clusters if species == "Lantana" else juliflora_clusters)
    st.dataframe(cluster_df[["Region", "Area_km2", "Description"]], hide_index=True)
