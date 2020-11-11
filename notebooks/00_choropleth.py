# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.5.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# +
import json

import folium
import geopandas as gpd
import requests
# -

geojson_url = "http://www.openculture.gov.tn/dataset/39ee59b8-f5b5-4459-b5fc-a9d31f23c385/resource/0a2d20fb-fca4-4487-b457-3154f67c35e4/download/delegations-full.geojson"
geojson_url = "http://catalog.industrie.gov.tn/dataset/9910662a-4594-453f-a710-b2f339e0d637/resource/70f8c482-abdb-45f2-8f84-bb3f3955c5a3/download/tncirconscriptions.geojson"

geo_df = (
    gpd.read_file(geojson_url)
)
geo_df

m = folium.Map(location=[33.8869, 9.5375], zoom_start=6, zoom_control=False,)

folium.Choropleth(
    geo_data=geojson_url,
    name="choro",
    columns=[],
    key_on="properties.circo_id",
    data=geo_df,
    fill_color="YlGn",
).add_to(m)

m


