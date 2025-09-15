import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# Mock feed ingredient data
data = pd.DataFrame([
    {
        "ingredient": "Soy",
        "origin": "Mato Grosso, Brazil",
        "lat": -12.6819,
        "lon": -56.9211,
        "CO2e_kg": 6.1,
        "land_m2_kg": 2.8
    },
    {
        "ingredient": "Fish Oil",
        "origin": "Chimbote, Peru",
        "lat": -9.0745,
        "lon": -78.5936,
        "CO2e_kg": 3.2,
        "land_m2_kg": 0.1
    },
    {
        "ingredient": "Wheat",
        "origin": "Reims, France",
        "lat": 49.2628,
        "lon": 4.0347,
        "CO2e_kg": 1.4,
        "land_m2_kg": 1.0
    },
    {
        "ingredient": "Fish Meal",
        "origin": "Tema, Ghana",
        "lat": 5.6692,
        "lon": -0.0166,
        "CO2e_kg": 2.9,
        "land_m2_kg": 0.2
    },
    {
        "ingredient": "Rapeseed",
        "origin": "Saskatchewan, Canada",
        "lat": 52.9399,
        "lon": -106.4509,
        "CO2e_kg": 2.3,
        "land_m2_kg": 2.1
    }
])

st.set_page_config(page_title="Fish Feed Origin Map", layout="wide")

tab1, tab2, tab3 = st.tabs(["🌍 Feed Map", "📦 Total Footprint per Tonne of Fish", "🥩 Protein Comparison"])

with tab1:
    st.title("🌍 Fish Feed Ingredient Origins")
    st.markdown("This interactive map shows where the key ingredients in fish feed are sourced from globally. Hover over each point to view environmental impact metrics like carbon emissions and land use.")

    impact_metric = st.selectbox(
        "Select environmental impact to visualize:",
        options=["CO2e_kg", "land_m2_kg"],
        format_func=lambda x: "CO₂e per kg" if x == "CO2e_kg" else "Land use per kg"
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
        pickable=False,
        rounded=True,
        width_min_pixels=2,
        width_max_pixels=10
    )

    tooltip = {
        "html": """
        <b>{ingredient}</b><br/>
        Origin: {origin}<br/>
        CO₂e per kg: {CO2e_kg} kg<br/>
        Land use per kg: {land_m2_kg} m²
        """,
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
    }

    r = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
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
    with st.expander("📊 View Raw Data"):
        st.dataframe(data, use_container_width=True)


# --- Tab 2: Total Footprint per Tonne of Fish ---
with tab2:
    st.subheader("📦 Footprint of 1 Metric Tonne of Farmed Fish")

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
        co2 = data.loc[data["ingredient"] == ing, "CO2e_kg"].values[0] * pct * total_feed_needed
        land = data.loc[data["ingredient"] == ing, "land_m2_kg"].values[0] * pct * total_feed_needed
        co2_contributions[ing] = co2
        land_contributions[ing] = land

    total_CO2 = sum(co2_contributions.values())
    total_land = sum(land_contributions.values())

    st.metric("Total CO₂e", f"{total_CO2:,.0f} kg")
    st.metric("Total Land Use", f"{total_land:,.0f} m²")

    # Comparisons
    st.markdown("🛫 **Equivalent to 10 round-trip economy flights from Europe to Australia** (26.6 tonnes CO₂).")
    st.markdown("🗺️ **Equivalent to the size of East Timor** — that's the land area (~15,700 km²) needed globally to grow the feed for Norway's 2024 salmon production.")

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
### 🐟 National Impact of 2024 Norwegian Fish Farming (1.5 million tonnes)
""")
    
    norway_production = 1_500_000  # metric tonnes
    scaled_CO2 = total_CO2 * norway_production
    scaled_land = total_land * norway_production

    st.metric("Total CO₂e (Norway, 2024)", f"{scaled_CO2:,.0f} kg ({scaled_CO2/1_000_000:,.1f} million tonnes)")
    st.metric("Total Land Use (Norway, 2024)", f"{scaled_land:,.0f} m² ({scaled_land/1_000_000:,.1f} km²)")

    # Scaled comparisons
    scaled_flights = scaled_CO2 / 1000
    scaled_fields = scaled_land / 7000

    st.markdown(f"🛬 **That's equivalent to {scaled_flights:,.0f} round-trip flights** from Europe to Asia.")
    st.markdown("🗺️ **Equivalent to the land area of Montenegro ** — that's how much land was needed globally to grow the feed for Norway's 2024 salmon production.")

    # Map showing Luxembourg
    st.markdown("#### 📍 Approximate land area used by feed production:")

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
    st.subheader("🥩 Comparative Environmental Impact per 1 Tonne of Protein")

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