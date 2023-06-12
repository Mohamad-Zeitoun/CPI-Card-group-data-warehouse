import streamlit as st
import plotly.express as px
from dw import *
st.set_page_config(layout="wide")
sales = st.container()
# get locations names
locations = list()
for x in getLocations():
    (ele,) = x
    locations.insert(0, ele)
# get products names
product = list()
for x in getProducts():
    (ele,) = x
    product.insert(0, ele)
# get variance analysis information
varianceAnalysis = salesVarianceAnalysis()
with sales:
    locations = st.selectbox("Location Name", locations)
    location = []
    location.insert(0,locations)
    varianceAnalysis1 = varianceAnalysis.loc[varianceAnalysis['location name'].isin(location)]

    VarianceLine = px.line(varianceAnalysis1, x='year', y='amount variance', color='product', markers=True)
    st.plotly_chart(VarianceLine, use_container_width=True)
    VarianceLine.update_xaxes(tickformat="%Y")
