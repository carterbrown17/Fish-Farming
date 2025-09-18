import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# Mock feed ingredient data
data = pd.DataFrame([
    {"ingredient": "Soy Protein Concentrate", "origin": "Brazil", "lat": -10.0, "lon": -55.0, "CO2e_kg": 6.1, "land_m2_kg": 2.8, "share": 15},
    {"ingredient": "Fish Meal (Whole)", "origin": "Chimbote, Peru", "lat": -9.0745, "lon": -78.5936, "CO2e_kg": 3.2, "land_m2_kg": 0.1, "share": 12},
    {"ingredient": "Fish Meal (Trimmings)", "origin": "Norway", "lat": 63.5, "lon": 10.5, "CO2e_kg": 1.8, "land_m2_kg": 0.05, "share": 3.2},
    {"ingredient": "Faba Beans", "origin": "France", "lat": 46.2, "lon": 2.2, "CO2e_kg": 1.9, "land_m2_kg": 1.3, "share": 6.5},
    {"ingredient": "Wheat Gluten", "origin": "France", "lat": 48.8, "lon": 2.35, "CO2e_kg": 1.4, "land_m2_kg": 1.0, "share": 8},
    {"ingredient": "Sunflower Meal", "origin": "Ukraine", "lat": 48.4, "lon": 31.1, "CO2e_kg": 2.2, "land_m2_kg": 1.1, "share": 4.5},
    {"ingredient": "Pea Protein", "origin": "Canada", "lat": 52.9, "lon": -106.5, "CO2e_kg": 2.0, "land_m2_kg": 1.5, "share": 0.8},
    {"ingredient": "Guar Meal", "origin": "India", "lat": 27.0, "lon": 75.0, "CO2e_kg": 2.7, "land_m2_kg": 1.6, "share": 8.3},
    {"ingredient": "Fish Material", "origin": "Ghana", "lat": 7.95, "lon": -1.02, "CO2e_kg": 2.9, "land_m2_kg": 0.2, "share": 6},
])

st.set_page_config(page_title="Fish Feed Origin Map", layout="wide")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Feed Map",
    "Total Footprint per Tonne of Fish",
    "Protein Comparison",
    "Farm Pollution Map",
    "Waste Population Equivalent"
])

with tab1:
    st.title("Fish Feed Ingredient Origins")
    st.markdown("This interactive map shows where the key ingredients in fish feed are sourced from globally. Hover over each point to view environmental impact metrics like carbon emissions and land use.")

    impact_metric = st.selectbox(
        "Select metric to visualize:",
        options=["CO2e_kg", "land_m2_kg", "share"],
        format_func=lambda x: {
            "CO2e_kg": "CO₂e per kg",
            "land_m2_kg": "Land use per kg",
            "share": "Feed Share (%)"
        }[x]
    )

    view_state = pdk.ViewState(latitude=10, longitude=0, zoom=1.2, pitch=30)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data,
        get_position="[lon, lat]",
        get_color="[255, 140, 0, 160]",
        get_radius=70000,
        pickable=True,
        auto_highlight=True,
    )

    norway_coords = [8.4689, 60.4720]  # Center of Norway (lon, lat)

    flow_data = data.copy()
    flow_data["target_lon"] = norway_coords[0]
    flow_data["target_lat"] = norway_coords[1]

    # Normalize CO2e for color mapping
    max_emission = data[impact_metric].max()
    min_emission = data[impact_metric].min()

    def co2_to_color(value):
        # Blue (low) to Red (high)
        ratio = (value - min_emission) / (max_emission - min_emission) if max_emission > min_emission else 0
        r = int(255 * ratio)
        g = int(128 * (1 - ratio))
        b = int(255 * (1 - ratio))
        return [r, g, b]

    flow_data["color"] = flow_data[impact_metric].apply(co2_to_color)

    flow_layer = pdk.Layer(
        "LineLayer",
        flow_data,
        get_source_position="[lon, lat]",
        get_target_position="[target_lon, target_lat]",
        get_color="color",
        get_width=f"{impact_metric} * 1.5",
        pickable=True,
        rounded=True,
        width_min_pixels=2,
        width_max_pixels=10
    )

    tooltip = {
        "html": """
        <b>{ingredient}</b><br/>
        Origin: {origin}<br/>
        CO₂e per kg: {CO2e_kg} kg<br/>
        Land use per kg: {land_m2_kg} m²<br/>
        Feed share: {share}%
        """,
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
    }

    r = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=view_state,
        layers=[layer, flow_layer],
        tooltip=tooltip
    )

    st.markdown("**Note**: Arrow direction is from source to Norway.")
    st.markdown("""<div style='position: absolute; top: 90px; right: 30px; background: white; padding: 10px; border: 1px solid #ccc; border-radius: 8px; font-size: 0.9em; z-index: 999;'>
    <b>Line Legend</b><br>
    <span style='color: rgb(0,128,255);'>Blue</span> = Low impact<br>
    <span style='color: rgb(255,0,0);'>Red</span> = High impact<br>
    Thickness ∝ selected metric
    </div>""", unsafe_allow_html=True)
    st.pydeck_chart(r)

    # Optional: data table for reference
    with st.expander("View Raw Data"):
        st.dataframe(
            data.rename(columns={
                "CO2e_kg": "CO₂e (kg)",
                "land_m2_kg": "Land Use (m²)",
                "share": "Feed Share"
            }),
            use_container_width=True
        )


# --- Tab 2: Total Footprint per Tonne of Fish ---
with tab2:
    st.subheader("Footprint of 1 Metric Tonne of Farmed Fish")

    # Assume FCR = 1.2 (1.2 kg feed → 1 kg fish)
    total_feed_needed = 7200  # kg

    blend = {
        "Soy": 0.35,
        "Fish Oil": 0.10,
        "Wheat": 0.20,
        "Fish Meal": 0.25,
        "Rapeseed": 0.10
    }

    co2_contributions = {}
    land_contributions = {}

    for ing, pct in blend.items():
        match = data[data["ingredient"].str.contains(ing, case=False)]
        if not match.empty:
            co2 = match["CO2e_kg"].values[0] * pct * total_feed_needed
            land = match["land_m2_kg"].values[0] * pct * total_feed_needed
            co2_contributions[ing] = co2
            land_contributions[ing] = land
        else:
            st.warning(f"Ingredient '{ing}' not found in data. Skipping...")

    total_CO2 = sum(co2_contributions.values())
    total_land = sum(land_contributions.values())

    st.metric("Total CO₂e", f"{total_CO2:,.0f} kg")
    st.metric("Total Land Use", f"{total_land:,.0f} m²")

    # Comparisons
    st.markdown("**Equivalent to 10 round-trip economy flights from Europe to Australia** (26.6 tonnes CO₂).")
    st.markdown("**Equivalent to the size of East Timor** — that's the land area (~15,700 km²) needed globally to grow the feed for Norway's 2024 salmon production.")

    st.markdown("Ingredient contribution breakdown:")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**CO₂e Contribution**")
        fig1, ax1 = plt.subplots()
        pd.Series(co2_contributions).sort_values().plot.barh(ax=ax1, color='tomato')
        ax1.set_title("CO₂e Contribution (kg)")
        ax1.set_xlabel("kg CO₂e")
        st.pyplot(fig1)
    with col2:
        st.markdown("**Land Use Contribution**")
        fig2, ax2 = plt.subplots()
        pd.Series(land_contributions).sort_values().plot.barh(ax=ax2, color='forestgreen')
        ax2.set_title("Land Use Contribution (m²)")
        ax2.set_xlabel("Land use (m²)")
        st.pyplot(fig2)

    # --- Scaled Impact Section ---
    st.markdown("""
---
### National Impact of 2024 Norwegian Fish Farming (1.5 million tonnes)
""")
    
    norway_production = 1_500_000  # metric tonnes
    scaled_CO2 = total_CO2 * norway_production
    scaled_land = total_land * norway_production

    st.metric("Total CO₂e (Norway, 2024)", f"{scaled_CO2:,.0f} kg ({scaled_CO2/1_000_000:,.1f} million tonnes)")
    st.metric("Total Land Use (Norway, 2024)", f"{scaled_land:,.0f} m² ({scaled_land/1_000_000:,.1f} km²)")

    # Scaled comparisons
    scaled_flights = scaled_CO2 / 1000
    scaled_fields = scaled_land / 7000

    st.markdown(f"**That's equivalent to {scaled_flights:,.0f} round-trip flights** from Europe to Asia.")
    st.markdown("**Equivalent to the land area of Montenegro ** — that's how much land was needed globally to grow the feed for Norway's 2024 salmon production.")

    # Map showing Luxembourg
    st.markdown("#### Approximate land area used by feed production:")

    m = folium.Map(location=[49.8153, 6.1296], zoom_start=7)
    folium.GeoJson(
        data="""{
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[3.0,49.4],[4.6,49.4],[4.6,51.0],[3.0,51.0],[3.0,49.4]]]
            },
            "properties": {"name": "Luxembourg"}
        }""",
        style_function=lambda x: {
            "fillColor": "#ff7800",
            "color": "#ff7800",
            "weight": 2,
            "fillOpacity": 0.4
        },
        tooltip="Approx. 15,700 km² (similar to Montenegro or The Bahamas)"
    ).add_to(m)

    st_folium(m, width=700)

with tab3:
    st.subheader("Comparative Environmental Impact per 1 Tonne of Protein")

    # Mock values (in kg CO2e and land use in m2) per 1 tonne of protein
    protein_data = pd.DataFrame({
        "Protein": ["Salmon (farmed)", "Poultry", "Pork", "Beef"],
        "CO2e_kg": [total_CO2, 6_000, 12_000, 60_000],
        "Land_m2": [total_land, 4_500, 8_000, 160_000]
    })

    st.markdown("Environmental impact of producing 1 tonne of edible protein from different sources:")

    st.markdown("""<div style='background-color: #f9f9f9; padding: 10px; border-left: 5px solid #ccc;'>
    <b>Legend:</b><br>
    <span style='color: indianred;'>■</span> CO₂e Emissions (kg)<br>
    <span style='color: seagreen;'>■</span> Land Use (m²)
    </div>""", unsafe_allow_html=True)

    co2_chart = protein_data.set_index("Protein")["CO2e_kg"].sort_values().plot(kind='barh', color="indianred", title="CO₂e Emissions (kg)")
    st.pyplot(co2_chart.figure)

    land_chart = protein_data.set_index("Protein")["Land_m2"].sort_values().plot(kind='barh', color="seagreen", title="Land Use (m²)")
    st.pyplot(land_chart.figure)

with tab4:
    st.subheader("Pollution from Norwegian Fish Farms")

    # Mock farm locations with pollution levels
    pollution_data = pd.DataFrame({
        "farm": ["Farm A", "Farm B", "Farm C", "Farm D"],
        "lat": [62.55, 62.7, 63.2, 62.9],
        "lon": [6.2, 5.8, 7.6, 8.1],
        "pollution_index": [80, 55, 30, 75]
    })

    def color_by_pollution(val):
        if val > 70:
            return "red"
        elif val > 40:
            return "orange"
        else:
            return "green"

    pollution_data["color"] = pollution_data["pollution_index"].apply(color_by_pollution)

    m_pollution = folium.Map(location=[62.5, 10.5], zoom_start=6)
    for _, row in pollution_data.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=row["color"],
            fill=True,
            fill_opacity=0.7,
            tooltip=f"{row['farm']} (Pollution Index: {row['pollution_index']})"
        ).add_to(m_pollution)

    st_folium(m_pollution, width=700)

with tab5:
    st.subheader("Waste Output Comparison")

    st.markdown("Norway's fish farms produce sewage waste equivalent to a country with a population of **~50 million people**.")

    col1, col2 = st.columns([3, 2])
    with col1:
        m_eq = folium.Map(location=[49.0, 15.0], zoom_start=2)
        countries = {
            "Norway": [60.5, 8.5],
            "Spain": [40.4, -3.7],
            "South Korea": [36.5, 127.8],
            "Kenya": [1.3, 38.0]
        }
        for country, coords in countries.items():
            folium.CircleMarker(
                location=coords,
                radius=10,
                color="#de2d26" if country != "Norway" else "#3182bd",
                fill=True,
                fill_opacity=0.8,
                popup=country
            ).add_to(m_eq)
        st_folium(m_eq, width=700)
    with col2:
        st.markdown("### Population Comparison")
        st.markdown("""
        - **Norway**: 5.5 million  
        - **Fish Farm Waste Equivalent**: 50 million  
        - **Spain**: 47.6 million  
        - **South Korea**: 51.7 million  
        - **Kenya**: 54.4 million  
        """)