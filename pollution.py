import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Fish Farm Pollution Impact", layout="wide")
st.title("💩 Pollution from Norwegian Fish Farming")

st.markdown("Norway's fish farms produce **sewage waste equivalent to a human population of ~50 million people**.")

tab1, tab2 = st.tabs(["📊 Bar Chart", "🗺️ Map Comparison"])

# Tab 1: Bar chart comparison
with tab1:
    st.subheader("📊 Sewage Equivalent vs Country Populations")

    data = pd.DataFrame({
        "Label": ["Norway population", "Fish farm sewage", "Spain", "South Korea", "Kenya"],
        "Population (millions)": [5.5, 50, 47.6, 51.7, 54.4]
    })

    fig, ax = plt.subplots()
    data.set_index("Label").plot(kind="barh", ax=ax, color=["#6baed6", "#de2d26", "#969696", "#969696", "#969696"])
    ax.set_title("Fish Farm Sewage vs Country Populations")
    ax.set_xlabel("Population Equivalent (Millions)")
    st.pyplot(fig)

# Tab 2: Map with highlighted countries
with tab2:
    st.subheader("🗺️ Norway vs Countries with ~50M People")

    m = folium.Map(location=[20, 0], zoom_start=2)

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
            popup=f"{country}"
        ).add_to(m)

    st.markdown("Countries with a similar population to the waste produced by Norwegian fish farms:")
    col1, col2 = st.columns([3, 2])
    with col1:
        st_folium(m, width=700)
    with col2:
        st.markdown("### 📘 Population Legend")
        st.markdown("""
        - **Norway**: 5.5 million  
        - **Fish Farm Waste Equivalent**: 50 million  
        - **Spain**: 47.6 million  
        - **South Korea**: 51.7 million  
        - **Kenya**: 54.4 million  
        """)