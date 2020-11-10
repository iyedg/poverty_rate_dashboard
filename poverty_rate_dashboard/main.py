import pandas as pd
import plotly.io as pio
import streamlit as st
from pyprojroot import here

pio.templates.default = "plotly_white"

st.set_page_config(layout="wide")
st.header("Poverty rate dashboard")


st.dataframe(pd.read_csv(here("data/processed/poverty_rate_Tunisia_2020.csv")))
