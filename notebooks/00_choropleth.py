# -*- coding: utf-8 -*-
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
from itertools import product
from typing import Callable, Iterable, List, Union

import altair as alt
import geopandas as gpd
import numpy as np
import pandas as pd
import textdistance
from glom import Merge, T, glom
from scipy.optimize import linear_sum_assignment


# -

# ##  String matching

# +
def fuzzy_matching_best(
    source: Iterable,
    target: List[str],
    key: Callable = lambda x: x,
    scorer: Callable = textdistance.jaro_winkler.distance,
    maximize: bool = False,
):
    # The key functionality is added thanks to https://stackoverflow.com/a/18296812

    diff_source = source
    diff_target = target

    pairs = product(diff_source, diff_target)

    scores = np.array([scorer(key(q), c) for q, c in pairs]).reshape(
        (len(diff_source), len(diff_target))
    )

    row_ind, col_ind = linear_sum_assignment(scores, maximize)

    return [
        {"source": diff_source[i], "target": diff_target[j], "distance": scores[i, j]}
        for i, j in zip(row_ind, col_ind)
    ]


def fuzzy_match(
    df: pd.DataFrame,
    source_column: Union[str, int],
    target: Iterable[str],
    scorer: Callable = textdistance.jaro_winkler.distance,
    key: Callable = lambda x: x,
    maximize: bool = False,
    debug=False,
):
    source = df[source_column].astype("str").unique()

    source_diff = list(set(source) - set(target))
    target_diff = list(set(target) - set(source))

    matches = fuzzy_matching_best(
        source=source_diff,
        target=target_diff,
        key=key,
        scorer=scorer,
        maximize=maximize,
    )

    replacements_spec = Merge([{T["source"]: "target"}])
    replacements_dict = glom(matches, replacements_spec)

    distances_spec = ([{T["source"]: "distance"}], Merge())
    distances_dict = glom(matches, distances_spec)

    if debug:
        debug_col_name = f"{source_column}_match_from_target"
        return df.pipe(
            lambda df: df.assign(
                **{
                    debug_col_name: df[source_column].replace(replacements_dict),
                    "distance": df[source_column]
                    .replace(distances_dict)
                    .replace(r"\D+", 0, regex=True),
                }
            )
        ).set_index([source_column, debug_col_name, "distance"])
    else:
        return df.pipe(
            lambda df: df.assign(
                **{source_column: df[source_column].replace(replacements_dict)}
            )
        )


# -

# ## Load data

data_df = pd.read_csv(
    "/home/iyed/Projects/Personal/poverty_rate_dashboard/data/processed/poverty_rate_Tunisia_2020.csv"
).pipe(lambda df: df.assign(**{"Délégation": df["Délégation"].str.title()}))
data_df

geojson_url = "https://www.data4tunisia.org/s/resources/decoupage-de-la-tunisie-geojson-et-shapefile/20180505-120515/delegations-full.geojson"

geo_df = (
    gpd.read_file(geojson_url)
    .pipe(lambda df: df.loc[-df["type_2"].str.contains("Water")])
    .dropna(subset=["deleg_na_1"])
)
geo_df


# ## Match data

def sequential_fuzzy_match(
    df: pd.DataFrame,
    source_cols: List[Union[str, int]],
    target_cols: List[Iterable],
    *args,
    **kwargs
) -> pd.DataFrame:
    result_df = df.copy()
    for source_col, target_col in zip(source_cols, target_cols):
        result_df = fuzzy_match(result_df, source_col, target_col, *args, **kwargs)
    return result_df


matched_data_df = sequential_fuzzy_match(
    data_df,
    source_cols=["Gouvernorat", "Délégation"],
    target_cols=[geo_df["gov_name_f"], geo_df["deleg_na_1"]],
    scorer=textdistance.jaccard.normalized_distance,
)

matched_data_df.shape

data_df.shape

aug_df = geo_df.merge(
    matched_data_df,
    left_on=["gov_name_f", "deleg_na_1"],
    right_on=["Gouvernorat", "Délégation"],
    how="inner",
)
aug_df

aug_df.shape

import plotly.express as px

geo_df.columns

id_col = "adm_id"
fig = px.choropleth(
    aug_df,
    geojson=geojson_url,
    featureidkey=f"properties.{id_col}",
    projection="mercator",
    locations=id_col,
    hover_data=["deleg_name"],
    color="Taux de pauvreté",
    color_continuous_scale=px.colors.sequential.Viridis,
    height=1200,
)
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig

fig.write_html("plotly_choropleth.html")

# +
# aug_df.crs = {"init": "epsg:27700"}
# aug_df = aug_df.to_crs({"init": "epsg:4326"})

# define inline geojson data object
data_geojson = alt.InlineData(
    values=aug_df.to_json(), format=alt.DataFormat(property="features", type="json")
)

# chart object
poverty_chart = (
    alt.Chart(data_geojson)
    .mark_geoshape()
    .encode(
        color=alt.Color("properties.Taux de pauvreté:Q", legend=alt.Legend(columns=2),),
        tooltip=[
            "properties.Délégation:N",
            "properties.Gouvernorat:N",
            "properties.Taux de pauvreté:Q",
        ],
    )
    .properties(width=500, height=700)
)

school_chart = (
    alt.Chart(data_geojson)
    .mark_geoshape()
    .encode(
        color=alt.Color(
            "properties.Abandon primaire et secondaire %:Q",
            legend=alt.Legend(columns=2),
        ),
        tooltip=[
            "properties.Délégation:N",
            "properties.Gouvernorat:N",
            "properties.Abandon primaire %:Q",
        ],
    )
    .properties(width=500, height=700)
)
# -

alt.hconcat(poverty_chart, school_chart).resolve_scale("independent")


