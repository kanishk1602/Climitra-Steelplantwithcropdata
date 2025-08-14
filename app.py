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

@st.cache_data
def load_geocoded_companies():
    try:
        df = pd.read_excel("geocoded_combined_companies.xlsx")
        # Clean up any invalid coordinates
        df = df.dropna(subset=["Latitude", "Longitude"])
        df = df[(df["Latitude"].abs() <= 90) & (df["Longitude"].abs() <= 180)]
        return df
    except Exception as e:
        st.error(f"Error loading geocoded companies data: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def load_ricemill_data():
    try:
        df = pd.read_csv("ricemills.csv")
        # Clean up any invalid coordinates
        df = df.dropna(subset=["lat", "lng"])
        df = df[(df["lat"].abs() <= 90) & (df["lng"].abs() <= 180)]
        return df
    except Exception as e:
        st.error(f"Error loading ricemill data: {str(e)}")
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

if section == "Dashboard":
    st.title("🗺️ Biochar Cluster Map with Industrial Data and GeoJSON Overlays")
    
    # UPDATED: Data source selector with Rice Mills
    data_source = st.selectbox(
        "Select Data Source:",
        ["Steel Plants", "Geocoded Companies", "Rice Mills"],
        help="Choose between steel plant data, geocoded companies data, or rice mills data"
    )
    
    # Load appropriate data based on selection
    if data_source == "Steel Plants":
        plants = load_steel_plants()
        st.markdown("### Visualizing invasive species clusters and steel plants")
    elif data_source == "Geocoded Companies":
        plants = load_geocoded_companies()
        st.markdown("### Visualizing invasive species clusters and geocoded companies")
    else:  # Rice Mills
        plants = load_ricemill_data()
        st.markdown("### Visualizing invasive species clusters and rice mills")

    with st.expander("Data Debug Info"):
        st.write(f"Loaded {len(plants)} records from {data_source.lower()}")
        st.dataframe(plants)
        if data_source == "Steel Plants":
            invalid_coords = plants[(plants["latitude"].abs() > 90) | (plants["longitude"].abs() > 180)]
        elif data_source == "Rice Mills":
            invalid_coords = plants[(plants["lat"].abs() > 90) | (plants["lng"].abs() > 180)]
        else:
            invalid_coords = plants[(plants["Latitude"].abs() > 90) | (plants["Longitude"].abs() > 180)]
        if not invalid_coords.empty:
            st.warning(f"Found {len(invalid_coords)} records with invalid coordinates:")
            st.dataframe(invalid_coords)

    # --- FILTER WIDGETS ---
    st.markdown(f"#### 🔍 Filter {data_source} Data")
    
    if data_source == "Steel Plants":
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
            
    elif data_source == "Rice Mills":
        # Filters for rice mills
        name_filter = st.text_input("Search Rice Mill Name")
        if "state" in plants.columns:
            state_filter = st.multiselect("State", options=plants["state"].dropna().unique())
        else:
            state_filter = []
        if "country" in plants.columns:
            country_filter = st.multiselect("Country", options=plants["country"].dropna().unique())
        else:
            country_filter = []
        if "primary_category_name" in plants.columns:
            category_filter = st.multiselect("Category", options=plants["primary_category_name"].dropna().unique())
        else:
            category_filter = []

        filtered_plants = plants.copy()
        if name_filter:
            filtered_plants = filtered_plants[filtered_plants["name"].str.contains(name_filter, case=False, na=False)]
        if state_filter:
            filtered_plants = filtered_plants[filtered_plants["state"].isin(state_filter)]
        if country_filter:
            filtered_plants = filtered_plants[filtered_plants["country"].isin(country_filter)]
        if category_filter:
            filtered_plants = filtered_plants[filtered_plants["primary_category_name"].isin(category_filter)]
            
    else:
        # Filters for geocoded companies
        name_filter = st.text_input("Search Company Name")
        if "State_Province" in plants.columns:
            state_filter = st.multiselect("State/Province", options=plants["State_Province"].dropna().unique())
        else:
            state_filter = []
        if "Country" in plants.columns:
            country_filter = st.multiselect("Country", options=plants["Country"].dropna().unique())
        else:
            country_filter = []

        filtered_plants = plants.copy()
        if name_filter:
            filtered_plants = filtered_plants[filtered_plants["Company_Name"].str.contains(name_filter, case=False, na=False)]
        if state_filter:
            filtered_plants = filtered_plants[filtered_plants["State_Province"].isin(state_filter)]
        if country_filter:
            filtered_plants = filtered_plants[filtered_plants["Country"].isin(country_filter)]

    # --- DISPLAY SEARCH RESULTS ---
    if name_filter and not filtered_plants.empty:
        st.markdown("---")
        st.markdown(f"#### ℹ️ Details for Found {data_source}")
        for index, row in filtered_plants.iterrows():
            if data_source == "Steel Plants":
                with st.expander(f"{row['Plant Name']}"):
                    st.write(f"**Capacity (MTPA):** {row.get('Capacity(MTPA)', 'N/A')}")
                    st.write(f"**Furnace Type:** {row.get('Furnance', 'N/A')}")
                    st.write(f"**Operational Status:** {row.get('Operational', 'N/A')}")
                    source_url = row.get('Source')
                    if isinstance(source_url, str) and source_url.startswith('http'):
                        st.markdown(f"**Source:** <a href='{source_url}' target='_blank'>Visit Link</a>", unsafe_allow_html=True)
                    else:
                        st.write(f"**Source:** {source_url if pd.notna(source_url) else 'N/A'}")
                        
            elif data_source == "Rice Mills":
                with st.expander(f"{row['name']}"):
                    st.write(f"**Address:** {row.get('address', 'N/A')}")
                    st.write(f"**Phone:** {row.get('phone', 'N/A')}")
                    st.write(f"**Email:** {row.get('email', 'N/A')}")
                    st.write(f"**State:** {row.get('state', 'N/A')}")
                    st.write(f"**Country:** {row.get('country', 'N/A')}")
                    st.write(f"**ZIP:** {row.get('zip', 'N/A')}")
                    st.write(f"**Rating:** {row.get('star_count', 'N/A')} ({row.get('rating_count', 'N/A')} reviews)")
                    st.write(f"**Category:** {row.get('primary_category_name', 'N/A')}")
                    
                    # Website link
                    website_url = row.get('url')
                    if isinstance(website_url, str) and website_url.startswith('http'):
                        st.markdown(f"**Website:** <a href='{website_url}' target='_blank'>Visit Site</a>", unsafe_allow_html=True)
                    else:
                        st.write(f"**Website:** {website_url if pd.notna(website_url) else 'N/A'}")
                    
                    # Social media links
                    social_links = []
                    if pd.notna(row.get('facebook_link')) and row.get('facebook_link').startswith('http'):
                        social_links.append(f"<a href='{row['facebook_link']}' target='_blank'>Facebook</a>")
                    if pd.notna(row.get('instagram_link')) and row.get('instagram_link').startswith('http'):
                        social_links.append(f"<a href='{row['instagram_link']}' target='_blank'>Instagram</a>")
                    if pd.notna(row.get('twitter_link')) and row.get('twitter_link').startswith('http'):
                        social_links.append(f"<a href='{row['twitter_link']}' target='_blank'>Twitter</a>")
                    if pd.notna(row.get('linkedin_link')) and row.get('linkedin_link').startswith('http'):
                        social_links.append(f"<a href='{row['linkedin_link']}' target='_blank'>LinkedIn</a>")
                    if pd.notna(row.get('youtube_link')) and row.get('youtube_link').startswith('http'):
                        social_links.append(f"<a href='{row['youtube_link']}' target='_blank'>YouTube</a>")
                    if pd.notna(row.get('whatsapp_link')) and row.get('whatsapp_link').startswith('http'):
                        social_links.append(f"<a href='{row['whatsapp_link']}' target='_blank'>WhatsApp</a>")
                    if pd.notna(row.get('tiktok_link')) and row.get('tiktok_link').startswith('http'):
                        social_links.append(f"<a href='{row['tiktok_link']}' target='_blank'>TikTok</a>")
                    
                    if social_links:
                        st.markdown(f"**Social Media:** {' | '.join(social_links)}", unsafe_allow_html=True)
                        
            else:
                with st.expander(f"{row['Company_Name']}"):
                    st.write(f"**Sales Revenue:** {row.get('Sales_Revenue', 'N/A')}")
                    st.write(f"**City:** {row.get('City', 'N/A')}")
                    st.write(f"**State:** {row.get('State_Province', 'N/A')}")
                    st.write(f"**Country:** {row.get('Country', 'N/A')}")
                    company_url = row.get('Company_URL')
                    if isinstance(company_url, str) and company_url.startswith('http'):
                        st.markdown(f"**Website:** <a href='{company_url}' target='_blank'>Visit Site</a>", unsafe_allow_html=True)
                    else:
                        st.write(f"**Website:** {company_url if pd.notna(company_url) else 'N/A'}")
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
        # Set up map parameters based on data source
        if data_source == "Steel Plants":
            lat_col, lon_col, hover_name_col = "latitude", "longitude", "Plant Name"
        elif data_source == "Rice Mills":
            lat_col, lon_col, hover_name_col = "lat", "lng", "name"
        else:
            lat_col, lon_col, hover_name_col = "Latitude", "Longitude", "Company_Name"
        
        fig = px.scatter_mapbox(
            filtered_plants,
            lat=lat_col,
            lon=lon_col,
            hover_name=hover_name_col,
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
            st.markdown(f"""
            - 🟣 **Purple**: {data_source}  
            - 🟠 **Orange**: Primary GeoJSON Overlay  
            - 🔵 **Blue**: Comparison GeoJSON Overlay
            """)

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"No {data_source.lower()} data available or after filtering.")

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
