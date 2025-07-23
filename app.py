import plotly.express as px
import pandas as pd
import math
import streamlit as st
import json
import os
from PIL import Image
import base64
import streamlit.components.v1 as components
from streamlit_pdf_viewer import pdf_viewer

st.set_page_config(page_title="Biochar Dashboard")

st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-size: 13px !important;
    }
    .block-container {
        padding: 0.5rem 1rem 0.5rem 1rem;
    }
    .stSidebar {
        width: 220px !important;
    }
    .stDataFrame {
        font-size: 12px !important;
    }
    h1, h2, h3 {
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

if "show_sidebar" not in st.session_state:
    st.session_state["show_sidebar"] = True

if st.button("👈 Toggle Sidebar"):
    st.session_state["show_sidebar"] = not st.session_state["show_sidebar"]

section = "Dashboard"
if st.session_state["show_sidebar"]:
    with st.sidebar:
        section = st.radio("Navigate", ["Dashboard", "Crop-Specific Data"])

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

@st.cache_data
def load_steel_plants():
    try:
        df = pd.read_excel("steel_plant_data.xlsx")

        def to_decimal(coord):
            try:
                if isinstance(coord, str) and "°" in coord:
                    parts = coord.replace("°", " ").replace("'", " ").replace('"', " ").split()
                    deg, min_, sec, direction = int(parts[0]), int(parts[1]), float(parts[2]), parts[3]
                    decimal = deg + min_/60 + sec/3600
                    return -decimal if direction in ["S", "W"] else decimal
                return float(coord)
            except:
                return None

        df["latitude"] = df["Latitude"].apply(to_decimal)
        df["longitude"] = df["Longitude"].apply(to_decimal)

        df = df.dropna(subset=["latitude", "longitude"])
        return df
    except Exception as e:
        st.error(f"Error loading steel plants data: {str(e)}")
        return pd.DataFrame()

geojson_metadata = {
    "lantanapresence.geojson": {
        "source": "Research Paper",
        "external_link": "https://doi.org/10.1016/j.gecco.2020.e01080",
        "recorded_time": "2020",
        "description": "This layer shows Lantana camara presence clusters extracted from satellite NDVI and field survey data in India.",
        "image_path": "lantana.png"
    },
    "juliflora.geojson": {
        "source": "Manual published by CAZRI, Jodhpur & HDRA, Coventry",
        "external_link": "https://www.researchgate.net/publication/244993994_Managing_Prosopis_juliflora_A_Technical_Manual",
        "recorded_time": "2001",
        "description": "These dots show distribution of juliflora across Indian Map",
        "image_path": "juliflora.png"
    },
    "cottonstalk.geojson": {
        "source": "Bhuvan Jaivoorja (ISRO)",
        "external_link": "https://bhuvan-app1.nrsc.gov.in/bioenergy/index.php",
        "recorded_time": "2016",
        "description": "Surplus Cotton Biomass shown in this layer.",
        "image_path": "Cotton.png"
    },
    "sugarcane.geojson": {
        "source": "Bhuvan Jaivoorja (ISRO)",
        "external_link": "https://bhuvan-app1.nrsc.gov.in/bioenergy/index.php",
        "recorded_time": "2016",
        "description": "Surplus Sugarcane Biomass shown in this layer.",
        "image_path": "sugarcane.png"
    },
    "maize.geojson": {
        "source": "ICRISAT",
        "external_link": "https://oar.icrisat.org/10759/1/maize%20yield%20India.pdf",
        "recorded_time": "2018",
        "description": "Major districts of maize in India with area sown.",
        "image_path": "Maize.png"
    },
    "bamboo.geojson": {
        "source": "Zenodo Dataset",
        "external_link": "https://doi.org/10.5281/zenodo.14671750",
        "recorded_time": "2025",
        "description": "Shows the Bamboo presence.",
        "image_path": "bamboo.png"
    }
}

plants = load_steel_plants()

if section == "Dashboard":
    st.title("🗺️ Biochar Cluster Map with Steel Plants and GeoJSON Overlays")
    st.markdown("### Visualizing invasive species clusters and steel plants")

    with st.expander("Data Debug Info"):
        st.write(f"Loaded {len(plants)} steel plants")
        st.dataframe(plants)
        invalid_coords = plants[(plants["latitude"].abs() > 90) | (plants["longitude"].abs() > 180)]
        if not invalid_coords.empty:
            st.warning(f"Found {len(invalid_coords)} plants with invalid coordinates:")
            st.dataframe(invalid_coords)

    # --- FILTER WIDGETS ---
    st.markdown("#### 🔍 Filter Steel Plant Data")
    name_filter = st.text_input("Search Plant Name")
    operational_filter = st.multiselect("Operational Status", options=plants["Operational"].dropna().unique())
    furnace_filter = st.multiselect("Furnace Type", options=plants["Furnance"].dropna().unique())

    filtered_plants = plants.copy()
    if name_filter:
        filtered_plants = filtered_plants[filtered_plants["Plant Name"].str.contains(name_filter, case=False, na=False)]
    if operational_filter:
        filtered_plants = filtered_plants[filtered_plants["Operational"].isin(operational_filter)]
    if furnace_filter:
        filtered_plants = filtered_plants[filtered_plants["Furnance"].isin(furnace_filter)]

    # --- NEW: DISPLAY SEARCH RESULTS ---
    # This block will show detailed info only when a user searches by name.
    if name_filter and not filtered_plants.empty:
        st.markdown("---")
        st.markdown(f"#### ℹ️ Details for Found Plant(s)")
        for index, row in filtered_plants.iterrows():
            with st.expander(f"{row['Plant Name']}"):
                st.write(f"**Capacity (MTPA):** {row.get('Capacity(MTPA)', 'N/A')}")
                st.write(f"**Furnace Type:** {row.get('Furnance', 'N/A')}")
                st.write(f"**Operational Status:** {row.get('Operational', 'N/A')}")
                source_url = row.get('Source')
                if isinstance(source_url, str) and source_url.startswith('http'):
                    st.markdown(f"**Source:** <a href='{source_url}' target='_blank'>Visit Link</a>", unsafe_allow_html=True)
                else:
                    st.write(f"**Source:** {source_url if pd.notna(source_url) else 'N/A'}")
        st.markdown("---")

    geojson_file1 = st.selectbox("Select Primary GeoJSON Overlay:", ["None"] + list(geojson_metadata.keys()), key="geo1")
    geojson_file2 = st.selectbox("Select Comparison GeoJSON Overlay (optional):", ["None"] + list(geojson_metadata.keys()), key="geo2")

    def show_metadata_and_image(geojson_file):
        meta = geojson_metadata.get(geojson_file, {})
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"#### ℹ️ Metadata for {geojson_file}")
            st.markdown(f"**Description:** {meta.get('description', 'N/A')}")
            st.markdown(f"**Source_link:** [Visit site]({meta.get('external_link', '#')})")
            st.markdown(f"**Recorded Time:** {meta.get('recorded_time', 'Unknown')}")
            st.markdown(f"**Source:** {meta.get('source', 'Unknown')}")
            if os.path.exists(geojson_file):
                with open(geojson_file, "r") as f:
                    geojson_text = f.read()
                st.download_button(f"Download {geojson_file}", geojson_text, file_name=geojson_file, mime="application/json")
        with col2:
            if os.path.exists(meta.get("image_path", "")):
                st.image(meta["image_path"], caption="Source Reference Map", use_column_width=True)

    if geojson_file1 != "None":
        show_metadata_and_image(geojson_file1)
    if geojson_file2 != "None":
        show_metadata_and_image(geojson_file2)

    if not filtered_plants.empty:
        fig = px.scatter_mapbox(
            filtered_plants,
            lat="latitude",
            lon="longitude",
            hover_name="Plant Name",
            # --- MODIFIED: Removed hover_data to keep hover clean ---
            zoom=4,
            height=500,
            mapbox_style="carto-positron",
            color_discrete_sequence=["purple"]
        )
        fig.update_layout(mapbox_center={"lat": 20.5937, "lon": 78.9629}, margin={"r":0,"t":0,"l":0,"b":0})

        overlay_colors = {
            geojson_file1: "rgba(255, 165, 0, 0.5)",
            geojson_file2: "rgba(0, 128, 255, 0.5)"
        }

        for geojson_file in [geojson_file1, geojson_file2]:
            if geojson_file != "None" and os.path.exists(geojson_file):
                with open(geojson_file) as f:
                    geojson_data = json.load(f)
                overlay_color = overlay_colors.get(geojson_file, "rgba(0,0,0,0.5)")
                for feature in geojson_data["features"]:
                    geom_type = feature["geometry"]["type"]
                    coords = feature["geometry"]["coordinates"]
                    if geom_type == "Polygon" and coords and coords[0]:
                        try:
                            lons, lats = zip(*coords[0])
                            fig.add_trace(px.line_mapbox(lat=list(lats)+[lats[0]], lon=list(lons)+[lons[0]], color_discrete_sequence=[overlay_color]).data[0])
                        except Exception as e:
                            st.warning(f"⚠️ Skipped polygon: {e}")
                    elif geom_type == "Point":
                        lon, lat = coords
                        fig.add_scattermapbox(lat=[lat], lon=[lon], mode="markers", marker=dict(size=8, color=overlay_color), name="GeoJSON Point", hovertext=json.dumps(feature["properties"]), hoverinfo="text")
                    elif geom_type == "MultiPolygon":
                        for polygon in coords:
                            if polygon and polygon[0]:
                                lons, lats = zip(*polygon[0])
                                fig.add_trace(px.line_mapbox(lat=list(lats)+[lats[0]], lon=list(lons)+[lons[0]], color_discrete_sequence=[overlay_color]).data[0])

        with st.expander("Legend"):
            st.markdown("""
            - 🟣 **Purple**: Steel Plants  
            - 🟠 **Orange**: Primary GeoJSON Overlay  
            - 🔵 **Blue**: Comparison GeoJSON Overlay
            """)

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No steel plant data available or after filtering.")

elif section == "Crop-Specific Data":
    st.title("🌾 Crop-Specific Biochar Resource Information")
    crop_selected = st.selectbox("Choose a Crop", ["Cotton", "Sugarcane", "Maize", "Juliflora", "Lantana","Bamboo"])

    pdf_map = {
        "Cotton": "cotton.pdf",
        "Sugarcane": "sugarcane.pdf",
        "Maize": "maize.pdf",
        "Juliflora": "Juliflora (1).pdf",
        "Lantana": "Lantana (1).pdf",
        "Bamboo": "bamboo.pdf",
    }

    if crop_selected in pdf_map and os.path.exists(pdf_map[crop_selected]):
        st.markdown(f"#### 📄 {crop_selected} Reference PDF")
        with open(pdf_map[crop_selected], "rb") as f:
            st.download_button(label=f"⬇️ Download {crop_selected} PDF", data=f.read(), file_name=pdf_map[crop_selected], mime="application/pdf")
        pdf_viewer(pdf_map[crop_selected])
    else:
        st.warning("No PDF available for this crop.")
