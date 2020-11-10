import pandas as pd
import plotly.io as pio
import streamlit as st
from pyprojroot import here
from tabula.errors import JavaNotFoundError


try:
    import tabula

    LOAD_FROM_CSV = False
except JavaNotFoundError:
    LOAD_FROM_CSV = True

pio.templates.default = "plotly_white"

st.set_page_config(layout="wide")
st.header("Poverty rate dashboard")

input_pdf_path = here("data/raw/Carte de la pauvreté en Tunisie_final.pdf")


def clean_header(df: pd.DataFrame) -> pd.DataFrame:
    header = [
        "Délégation",
        "Abandon primaire %",
        "Abandon secondaire %",
        "Abandon primaire et secondaire %",
        "Taux de pauvreté",
    ]
    return (
        df.iloc[3:]
        # .dropna(how="any", axis="index")
        # .dropna(how="all", axis="columns")
        .dropna(how="all", axis="columns")
        .dropna(thresh=3, axis="columns")
        .dropna(how="any", axis="index")
        .set_axis(header, axis="columns")
    )


def clean_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(
        **{
            k: pd.to_numeric(df[k].str.replace(",", "."))
            for k in filter(lambda x: x != "Délégation", df.columns)
        }
    )


def cleaning_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    return df.pipe(clean_header).pipe(clean_numeric_columns)


@st.cache()
def load_data():
    governorates_pages = {
        "Tunis": 40,
        "Ariana": 42,
        "Ben Arous": 44,
        "Manouba": 45,
        "Nabeul": 49,
        "Zagouan": 50,
        "Bizerte": 52,
        "Beja": 55,
        "Jandouba": 56,
        "Kef": 58,
        "Seliana": 62,
        "Sousse": 66,
        "Monastir": 68,
        "Mahdia": 69,
        "Sfax": 71,
        "Kairouan": 73,
        "Kasserine": 75,
        "Sidi Bouzid": 76,
        "Gabes": 79,
        "Médnine": 82,
        "Tataouine": 82,
        "Gafsa": 85,
        "Tozeur": 86,
        "Kebili": 87,
    }

    governorates_dfs = []

    for governorate_name, page in governorates_pages.items():
        if governorate_name == "Tataouine":
            table_index = 1
        else:
            table_index = 0
        df = (
            tabula.read_pdf(
                input_pdf_path,
                pages=page,
                multiple_tables=True,
                pandas_options={"header": None},
            )[table_index]
            .pipe(cleaning_pipeline)
            .assign(Gouvernorat=governorate_name)
        )

        governorates_dfs.append(df)
    combined_df = pd.concat(governorates_dfs, ignore_index=True)
    combined_df.to_csv(here("data/processed/poverty_rate_Tunisia_2020.csv"))
    return combined_df


if LOAD_FROM_CSV:
    st.dataframe(pd.read_csv(here("data/processed/poverty_rate_Tunisia_2020.csv")))
else:
    st.dataframe(load_data())
