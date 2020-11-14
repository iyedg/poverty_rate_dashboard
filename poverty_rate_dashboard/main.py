import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st
import textdistance
from pyprojroot import here
from string_matching import sequential_fuzzy_match

pio.templates.default = "plotly_white"

st.set_page_config(layout="wide")
st.sidebar.header("Carte de la pauvreté en Tunisie - 2020")


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

governorate_names = list(combined_df["Gouvernorat"].sort_values().unique())
governorate_names.append("Tout")

selected_governorate = st.sidebar.selectbox(
    "Gouvernorat", governorate_names, index=len(governorate_names) - 1
)


dependent_variable = st.sidebar.radio(
    "Variable dépendante",
    [
        "Abandon primaire et secondaire %",
        "Abandon secondaire %",
        "Abandon primaire %",
    ],
)


def subset_df(selected_governorate: str) -> pd.DataFrame:
    if selected_governorate != "Tout":
        filtered_df = combined_df.pipe(
            lambda df: df.loc[df["Gouvernorat"].str.contains(selected_governorate)]
        )
    else:
        filtered_df = combined_df
    return filtered_df.drop_duplicates(subset=["Gouvernorat", "Délégation"])


def plot_poverty_map(selected_governorate: str) -> None:
    if selected_governorate == "Tout":
        st.subheader(f"Taux de pauvreté par délégation")
    else:
        st.subheader(f"Taux de pauvreté par délégation à {selected_governorate}")

    filtered_df = subset_df(selected_governorate)
    id_col = "adm_id"

    fig = px.choropleth(
        filtered_df,
        geojson=geojson_url,
        featureidkey=f"properties.{id_col}",
        projection="mercator",
        locations=id_col,
        hover_data=["deleg_name"],
        color="Taux de pauvreté",
        color_continuous_scale=colorscale,
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    st.plotly_chart(fig, use_container_width=True)


def plot_regression(selected_governorate: str) -> None:
    if selected_governorate == "Tout":
        st.subheader(f"Taux de pauvreté par délégation")
    else:
        st.subheader(f"Taux de pauvreté par délégation à {selected_governorate}")
    filtered_df = subset_df(selected_governorate)
    fig = px.scatter(
        data_frame=filtered_df,
        x=dependent_variable,
        y="Taux de pauvreté",
        trendline="ols",
        color="Taux de pauvreté",
        color_continuous_scale=colorscale,
        hover_data=[
            "Gouvernorat",
            "Délégation",
            "Taux de pauvreté",
            dependent_variable,
        ],
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig)


def plot_bar(selected_governorate: str) -> None:
    if selected_governorate == "Tout":
        st.subheader(f"Taux de pauvreté par délégation")
    else:
        st.subheader(f"Taux de pauvreté par délégation à {selected_governorate}")
    fig = px.bar(
        subset_df(selected_governorate),
        x="Délégation",
        y="Taux de pauvreté",
        hover_data=[
            "Gouvernorat",
            "Délégation",
            "Taux de pauvreté",
            dependent_variable,
        ],
    )
    fig.update_layout(xaxis={"categoryorder": "total descending"})
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig, use_container_width=True)


colorscale = "Magma"
col1, col2 = st.beta_columns(2)


with col1:
    plot_regression(selected_governorate)
with col2:
    plot_poverty_map(selected_governorate)
plot_bar(selected_governorate)
