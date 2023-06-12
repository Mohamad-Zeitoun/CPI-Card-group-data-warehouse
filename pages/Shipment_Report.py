import streamlit as st
import plotly.express as px
from dw import *
years = list(["All"])
for i in getshYears():
    (element,) = i
    years.insert(len(years), element)
# Top Agents
numberOfTopSalesAgent = st.slider("Pick Top Percentage Performance Number of Sales Agent", 0, 100)
yearsList = st.multiselect('which years do you want?', years)
res = topSalesAgent(100-numberOfTopSalesAgent)
if 'All' in yearsList:
    TopAgents = res.groupby(['location', 'agent_name'])['success_lead'].sum() \
        .reset_index(name='success_lead').sort_values(by=['location', 'success_lead'], ascending=False)

else:
    TopAgents = res.loc[res['year'].isin(yearsList)].groupby(['location', 'agent_name'])['success_lead'].sum() \
        .reset_index(name='success_lead').sort_values(by=['location', 'success_lead'], ascending=False)
treeMap = px.treemap(data_frame=TopAgents, path=[px.Constant('All'), 'location', 'agent_name'], values='success_lead',
                     color_continuous_scale='RdBu', color='success_lead', range_color=(1, 4))
treeMap.update_traces(root_color="lightgrey")
st.plotly_chart(treeMap, use_container_width=True)

# Shipment Delays by Location
locations = list(["All"])
for i in getLocations():
    (element,) = i
    locations.insert(len(locations), element)

locationsList = st.multiselect('Select locations you want to show The Delays:', locations)
res = shipmentDelays()
if 'All' not in locationsList:
    shipment = res.loc[res['location_name'].isin(locationsList)]
    try:
        line_chart = px.line(shipment, 'year', 'Delays', markers=True,facet_col='location_name', color='location_name',facet_col_wrap=2
                             )
        line_chart.update_xaxes(tickformat="%Y")
    except:
        pass

else:
    shipment = res
    line_chart = px.line(shipment, 'year', 'Delays', markers=True, facet_col='location_name', color='location_name',
                         facet_col_wrap=2)
    line_chart.update_xaxes(tickformat="%Y")

try:
    st.plotly_chart(line_chart, use_container_width=True)
except:
    pass