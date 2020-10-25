import streamlit as st
import pandas as pd
import requests

import plotly.graph_objects as go
from plotly.subplots import make_subplots

@st.cache
def get_countries():
    api_uri = "https://covid19-eu-data-api-gamma.now.sh/api/countryLookup"
    data = requests.get(api_uri).json()
    countries = data["countries"]
    countries = [list(i.keys()) for i in countries]
    countries = sum(countries, [])

    countries = [i for i in countries if (len(i)==2) and (i != "uk")]

    return countries

@st.cache
def get_data(country_code, days):

    api_uri = f"https://covid19-eu-data-api-gamma.now.sh/api/countries?alpha2={country_code}&days={days+1}"

    data = requests.get(api_uri).json()

    return data

@st.cache
def create_dataframe(data):

    data_records = []

    for i in data:
        data_records += i.get("records")

    df = pd.DataFrame(data_records)
    # columns = ["country", "nuts_1", "cases", "cases/100k pop.", "deaths", "date"]
    # df = df[columns]
    df.rename(
        columns={
            "cases/100k pop.": "cases_per_100k"
        },
        inplace=True
    )

    return df

@st.cache
def forge_country_data(df, region_key=None):
    all_cols = df.columns
    region_cols = [i for i in all_cols if i.startswith("nuts_") or i.startswith("lau")]
    if region_key is None:
        region_key = region_cols[0]

    regions = list(df[region_key].unique())
    df_full = pd.DataFrame()
    for nut in regions:
        df_nut = df.loc[df[region_key] == nut].reset_index(drop=True)
        df_nut["date"] = pd.to_datetime(df_nut["date"]).apply(lambda x: x.date() )
        df_nut.sort_values(by="date", inplace=True)

        shifted_cols = [
            "previous_cases",
            # "previous_deaths",
            # "previous_cases_per_100k"
        ]
        df_nut_shifted = df_nut.shift(periods=1).rename(
            columns={
                "cases": "previous_cases",
                # "deaths": "previous_deaths",
                # "cases_per_100k": "previous_cases_per_100k"
            }
        ).copy()

        df_nut_merged = pd.merge(
            df_nut, df_nut_shifted[shifted_cols], how="left",
            left_index=True, right_index=True
        )
        df_nut_merged["new_cases"] = df_nut_merged.cases - df_nut_merged.previous_cases

        df_nut_merged.dropna(subset=["previous_cases"], inplace=True)
        df_full = pd.concat([df_full, df_nut_merged], ignore_index=True)


    full_merge_cols = ["country", "date"]
    df_full = pd.merge(
        df_full,
        df_full.groupby(
            full_merge_cols
        )["new_cases", "cases"].sum().reset_index().rename(
            columns={
                "new_cases": "country_new_cases",
                "cases": "country_cases",
                # "deaths": "country_deaths"
            }
        ),
        how="left", on=full_merge_cols
    )

    return df_full, regions, region_key


def create_case_fig(df_selected, title, left_axis=None, right_axis=None):

    if not left_axis:
        left_axis = {
            "column": "new_cases",
            "name": "New Cases",
            "label": "New Cases"
        }
    if not right_axis:
        right_axis = {
            "column": "cases",
            "name": "Cumulative Cases",
            "label": "Cumulative Cases"
        }

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=df_selected["date"], y=df_selected[
                left_axis.get("column")
            ],
            name=left_axis.get("name"),
            marker_color="firebrick"
        ), secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=df_selected["date"], y=df_selected[
                right_axis.get("column")
            ],
            name=right_axis.get("name"),
            marker={"color": "black"}
        ), secondary_y=True
    )

    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        yaxis=dict(
            title={
                "text": left_axis.get("label")
            },
            rangemode="tozero"
        ),
        yaxis2=dict(
            title={
                "text": left_axis.get("label")
            },
            rangemode="tozero"
        ),
        title={
            "text": title,
            "x": 0.5
        },
        font=dict(
            family="Courier New, monospace",
            size=18,
            color="#7f7f7f"
        )
    )

    return fig