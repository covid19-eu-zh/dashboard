import streamlit as st
from utils import forge_country_data as _forge_country_data
from utils import create_dataframe as _create_dataframe
from utils import get_data as _get_data
from utils import create_case_fig as _create_case_fig
from utils import get_countries as _get_countries


# Config the whole app
st.set_page_config(
    page_title="A Dashboard Template",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

#

country_code = "DE"
days = 5

# Calculate country codes
avaibale_countries = _get_countries()
country_codes = [i.upper() for i in avaibale_countries]

# Adjust sidebar

st.sidebar.markdown("## COVID-19 Cases in EU")

country_code = st.sidebar.selectbox(
    label="Select Country", options=country_codes,
    index=country_codes.index(country_code)
).lower()
available_days = list(range(1, 2*365))

days = st.sidebar.selectbox(
    label="Days", options=available_days, index=365
)


st.sidebar.markdown(
    "## About"
    "\n"
    "This is a simple dashboard to show the data we are collecting. \n"
    "- Raw data source: [covid19-eu-zh/covid19-eu-data](https://github.com/covid19-eu-zh/covid19-eu-data)"
    "\n"
    "- Data API: [covid19-eu-zh/covid19-eu-data-api](https://github.com/covid19-eu-zh/covid19-eu-data-api)"
    "\n"
    "- [source code](https://github.com/covid19-eu-zh/dashboard)"
)

# Get data
data = _get_data(country_code, days)
df = _create_dataframe(data)
# st.write(df)
df_full, regions, region_key = _forge_country_data(df)
# st.write(df_full)
# st.write(regions)
# st.write(region_key)

# st.write(df_full)
# st.write(regions)



def main(df_full):

    selected_region = "total"
    selected_region = st.selectbox(label="Regions", options=["total"]+regions )
    preview_columns = [
        "country", "date", "new_cases",
        "cases", # "deaths"
    ]
    if "cases_per_100k" in df_full:
        preview_columns = preview_columns + ["cases_per_100k"]

    show_data_table = st.checkbox('Show Data Table')

    if selected_region == "total":
        st.markdown(f"Data for the whole country")
        df_selected = df_full[
            [
                "country", "date", "country_new_cases", "country_cases",
                # "country_deaths"
            ]
        ].drop_duplicates()

        total_left_axis = {
            "column": "country_new_cases",
            "name": "New Cases",
            "label": "New Cases"
        }
        total_right_axis = {
            "column": "country_cases",
            "name": "Total Cases",
            "label": "Total Cases"
        }

        fig = _create_case_fig(
            df_selected, f"COVID-19 Cases for {country_code.upper()}", left_axis=total_left_axis, right_axis=total_right_axis
        )

        st.plotly_chart(fig, use_container_width=True)

        if show_data_table:
            st.table(df_selected)

    else:
        st.markdown(f"Selected region: {selected_region}")
        df_selected = df_full.loc[df_full[region_key] == selected_region][preview_columns]

        fig = _create_case_fig(df_selected, f"COVID-19 Cases for {selected_region} in {country_code.upper()}")

        st.plotly_chart(fig, use_container_width=True)

        if show_data_table:
            st.table(df_selected)

if __name__ == "__main__":
    main(df_full)
    pass

