import streamlit as st
import plotly.express as px
from dw import *
st.set_page_config(layout="wide")
prof = st.container()
# get locations names


profitMargin = profitMargin()
with prof:

    location = list(["All"])
    for x in getLocations():
        (ele,) = x
        location.insert(len(location), ele)
    locations = st.multiselect("Location Name", location)

    if 'All' not in locations:
        profitMargin = profitMargin.loc[profitMargin['location_name'].isin(locations)]

    VarianceLine = px.line(profitMargin, x='year', y='profit_margin', markers=True, facet_col='location_name',
                           color='location_name', facet_col_wrap=2)
    st.plotly_chart(VarianceLine, use_container_width=True)
