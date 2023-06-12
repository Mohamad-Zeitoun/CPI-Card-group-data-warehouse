import streamlit as st
import plotly.express as px
from dw import *
st.set_page_config(layout="wide")

# Invoice Report
invoiceReport = st.container()
years = list(["All"])
for i in getYears():
    (element,) = i
    years.insert(len(years), element)
with invoiceReport:
    yearsList = st.multiselect('which years do you want?', years)

    total_invoice_amount, invoice_count = st.columns(2)
    res = totalInvoice()
    if 'All' in yearsList:
        totalInvoice = res.sum(axis=0)
    else:
        totalInvoice = res.loc[res['year'].isin(yearsList)].sum(axis=0)

    with total_invoice_amount:
        st.metric('Total Invoice Amount', int(totalInvoice['invoice Amount']))

    with invoice_count:
        st.metric('Invoice Count', int(totalInvoice['count']))
    invoiceByLocation = invoiceAmountBylocation()

    # invoice by location ( Tree Map Chart )
    if 'All' in yearsList:
        invLocation = invoiceByLocation.groupby('location_name')['Invoice Amount'].sum() \
            .reset_index(name='Invoice Amount').sort_values(by='Invoice Amount', ascending=False)
    else:
        invLocation = invoiceByLocation.loc[invoiceByLocation['year'].isin(yearsList)].groupby('location_name')[
            'Invoice Amount'].sum() \
            .reset_index(name='Invoice Amount').sort_values(by='Invoice Amount', ascending=False)
    treeMap = px.treemap(data_frame=invLocation, path=[px.Constant('All'), 'location_name'], values='Invoice Amount',
                         color='Invoice Amount', color_continuous_scale='RdBu')
    st.plotly_chart(treeMap, use_container_width=True)

    # invoice by product
    invoiceProduct = invoiceAmountByProduct()
    if 'All' in yearsList:
        invProduct = invoiceProduct.groupby('sales_class_desc')['Invoice Amount'].sum() \
            .reset_index(name='Invoice Amount').sort_values(by='Invoice Amount', ascending=False)
    else:
        invProduct = invoiceProduct.loc[invoiceProduct['year'].isin(yearsList)].groupby('sales_class_desc')[
            'Invoice Amount'].sum() \
            .reset_index(name='Invoice Amount').sort_values(by='Invoice Amount', ascending=False)
    Barchart = px.bar(data_frame=invProduct, x='sales_class_desc', y='Invoice Amount', color='sales_class_desc')
    st.plotly_chart(Barchart, use_container_width=True)

topCustomer = st.slider("Cilck to show top customer by invoice", 0, 100)
yearsList1 = st.multiselect('Which years do you want?', years)

res = TopCustomer(100-topCustomer)

if 'All' in yearsList1:
    TopCust = res.groupby(['cust_key', 'cust_name'])['suminvoiceamt'].sum() \
        .reset_index(name='suminvoiceamt').sort_values(by=['cust_key', 'cust_name'], ascending=False)

else:
    TopCust = res.loc[res['year'].isin(yearsList1)].groupby(['cust_key', 'cust_name'])['suminvoiceamt'].sum() \
        .reset_index(name='suminvoiceamt').sort_values(by=['cust_key', 'cust_name'], ascending=False)
treeMap = px.treemap(data_frame=TopCust, path=[px.Constant('All'), 'cust_name'], values='suminvoiceamt',
                     color_continuous_scale='RdBu', color='suminvoiceamt')
treeMap.update_traces(root_color="lightgrey")
st.plotly_chart(treeMap, use_container_width=True)