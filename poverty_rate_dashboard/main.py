import textdistance
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st
from pyprojroot import here

from string_matching import sequential_fuzzy_match

pio.templates.default = "plotly_white"

st.set_page_config(layout="wide")
st.header("Poverty rate dashboard")

geojson_url = (
    "https://www.data4tunisia.org/s/resources/"
    "decoupage-de-la-tunisie-geojson-et-shapefile/"
    "20180505-120515/delegations-full.geojson"
)


@st.cache()
def get_poverty_data() -> pd.DataFrame:
    poverty_rate_df = pd.read_csv(
        here("data/processed/poverty_rate_Tunisia_2020.csv")
    ).pipe(lambda df: df.assign(**{"Délégation": df["Délégation"].str.title()}))
    return poverty_rate_df


@st.cache()
def get_geojson_data() -> gpd.GeoDataFrame:
    geo_df = gpd.read_file(geojson_url).dropna(subset=["deleg_name"])
    return geo_df


def combined_data() -> gpd.GeoDataFrame:
    data_df = get_poverty_data()
    geo_df = get_geojson_data()
    # Fuzzy string matching for shared ID columns
    matched_data_df = sequential_fuzzy_match(
        data_df,
        source_cols=["Gouvernorat", "Délégation"],
        target_cols=[geo_df["gov_name_f"], geo_df["deleg_na_1"]],
        scorer=textdistance.jaccard.normalized_distance,
    )
    aug_df = geo_df.merge(
        matched_data_df,
        left_on=["gov_name_f", "deleg_na_1"],
        right_on=["Gouvernorat", "Délégation"],
        how="inner",
    )
    return aug_df


combined_df = combined_data()

governorate = st.sidebar.selectbox(
    "Gouvernorat", combined_df["Gouvernorat"].sort_values().unique()
)

id_col = "adm_id"
fig = px.choropleth(
    combined_df.query(f"Gouvernorat == '{governorate}'"),
    geojson=geojson_url,
    featureidkey=f"properties.{id_col}",
    projection="mercator",
    locations=id_col,
    hover_data=["deleg_name"],
    color="Taux de pauvreté",
    color_continuous_scale=px.colors.sequential.thermal,
)
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

st.subheader(f"Taux de pauvreté par délégation à {governorate}")

st.plotly_chart(fig, use_container_width=True)
