import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st
from pyprojroot import here
import geopandas
import json

pio.templates.default = "plotly_white"

st.set_page_config(layout="wide")
st.header("Poverty rate dashboard")

poverty_rate_df = pd.read_csv(here("data/processed/poverty_rate_Tunisia_2020.csv"))

scatter_fig = px.scatter(
    poverty_rate_df,
    x="Abandon primaire et secondaire %",
    y="Taux de pauvreté",
    facet_col="Gouvernorat",
    facet_col_wrap=4,
    color="Gouvernorat",
    trendline="ols",
    height=2000,
)

decoupage = geopandas.read_file(
    here("data/resources/decoupage_delegations.json"), layer="delegations"
)

st.write(decoupage)

# st.dataframe(decoupage)

# with open(here("data/resources/decoupage_delegations.json")) as f:
# decoupage = json.load(f)

# st.json(decoupage)
