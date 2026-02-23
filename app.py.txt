import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")

st.title("Revenue & Profit Transition Simulator")

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.header("Business Mix")

custom_share = st.sidebar.slider("Custom Share (%)", 0, 100, 60)
product_share = 100 - custom_share

st.sidebar.write(f"Product Share automatically set to {product_share}%")

st.sidebar.header("Pricing Assumptions")

custom_price = st.sidebar.number_input("Custom Home Price ($)", value=1800000, step=50000)
product_price = st.sidebar.number_input("Product Home Price ($)", value=650000, step=25000)

custom_design_fee = st.sidebar.number_input("Custom Design Fee ($)", value=75000, step=5000)
product_design_fee = st.sidebar.number_input("Product Design Fee ($)", value=25000, step=2500)

st.sidebar.header("Margins")

custom_margin = st.sidebar.slider("Custom Gross Margin (%)", 0, 50, 22)
product_margin = st.sidebar.slider("Product Gross Margin (%)", 0, 50, 28)
design_margin = st.sidebar.slider("Design Margin (%)", 0, 80, 60)

st.sidebar.header("Volume & Growth")

starting_volume = st.sidebar.number_input("Annual Projects (Year 1)", value=20)
growth_rate = st.sidebar.slider("Annual Growth Rate (%)", 0, 20, 3)
years = st.sidebar.slider("Projection Years", 1, 10, 5)

st.sidebar.header("Overhead")

annual_overhead = st.sidebar.number_input("Annual Fixed Overhead ($)", value=8000000, step=500000)

# -----------------------------
# Calculations
# -----------------------------
data = []

for year in range(1, years + 1):
    total_projects = starting_volume * ((1 + growth_rate / 100) ** (year - 1))

    custom_projects = total_projects * (custom_share / 100)
    product_projects = total_projects * (product_share / 100)

    custom_revenue = custom_projects * custom_price
    product_revenue = product_projects * product_price

    custom_design_revenue = custom_projects * custom_design_fee
    product_design_revenue = product_projects * product_design_fee

    total_revenue = (
        custom_revenue + product_revenue +
        custom_design_revenue + product_design_revenue
    )

    gross_profit = (
        custom_revenue * custom_margin / 100 +
        product_revenue * product_margin / 100 +
        custom_design_revenue * design_margin / 100 +
        product_design_revenue * design_margin / 100
    )

    net_profit = gross_profit - annual_overhead

    data.append([
        year,
        total_projects,
        custom_revenue,
        product_revenue,
        custom_design_revenue + product_design_revenue,
        total_revenue,
        gross_profit,
        net_profit
    ])

df = pd.DataFrame(data, columns=[
    "Year", "Projects",
    "Custom Revenue", "Product Revenue", "Design Revenue",
    "Total Revenue", "Gross Profit", "Net Profit"
])

# -----------------------------
# KPI Row
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Final Year Revenue", f"${df['Total Revenue'].iloc[-1]:,.0f}")
col2.metric("Final Year Gross Profit", f"${df['Gross Profit'].iloc[-1]:,.0f}")
col3.metric("Final Year Net Profit", f"${df['Net Profit'].iloc[-1]:,.0f}")

# -----------------------------
# Charts
# -----------------------------
st.subheader("Total Revenue Over Time")
fig1 = px.line(df, x="Year", y="Total Revenue")
st.plotly_chart(fig1, use_container_width=True)

st.subheader("Revenue Composition")
fig2 = px.area(
    df,
    x="Year",
    y=["Custom Revenue", "Product Revenue", "Design Revenue"]
)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Profit Over Time")
fig3 = px.line(df, x="Year", y=["Gross Profit", "Net Profit"])
st.plotly_chart(fig3, use_container_width=True)

st.dataframe(df)