# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Revenue Forecast Dashboard", layout="wide")

st.title("Bensonwood Revenue Forecast Dashboard")

# --- SLIDERS WITH HOVER-HELP ---
custom_pct = st.slider(
    "Custom % of total business",
    min_value=0, max_value=100, value=60,
    help="Adjusts the proportion of custom homes versus product homes. Higher % = higher-margin custom work, lower % = more product volume."
)

product_price = st.slider(
    "Average Product Home Price",
    min_value=100000, max_value=2000000, step=10000, value=500000,
    help="Sets the average sale price for product homes. Affects total revenue and required volume to reach profit targets."
)

design_tier_price = st.slider(
    "Design Tier Service Price",
    min_value=5000, max_value=50000, step=1000, value=15000,
    help="Adjusts the average price for design services (tiers). Affects profit margins and revenue calculations."
)

time_horizon = st.slider(
    "Time Horizon (years)",
    min_value=1, max_value=10, value=5,
    help="Sets the length of the forecast in years. Longer horizons compound effects of margin shifts and volume changes."
)

# --- ASSUMED MARGINS ---
custom_margin = 0.35
product_margin = 0.15

# --- TIME SERIES ---
years = np.arange(1, time_horizon + 1)

# --- CALCULATIONS ---
custom_revenue = custom_pct/100 * (product_price + design_tier_price) * years
product_revenue = (100-custom_pct)/100 * product_price * years

total_revenue = custom_revenue + product_revenue

# Compute required volume for same profit if margins shift
base_profit = custom_revenue[-1]*custom_margin + product_revenue[-1]*product_margin
product_only_profit = total_revenue * product_margin
required_volume_multiplier = np.maximum(1, base_profit / product_only_profit)

profit_margin = (custom_revenue*custom_margin + product_revenue*product_margin) / total_revenue

split_ratio = custom_pct / 100 * np.ones_like(years)

# --- PLOTLY SUBPLOTS ---
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("Total Revenue", "Required Volume Multiplier", "Profit Margin", "Custom vs Product Split")
)

# Total Revenue
fig.add_trace(go.Scatter(x=years, y=total_revenue, mode='lines+markers', name="Revenue"), row=1, col=1)

# Required Volume Multiplier
fig.add_trace(go.Scatter(x=years, y=required_volume_multiplier, mode='lines+markers', name="Volume Factor"), row=1, col=2)

# Profit Margin
fig.add_trace(go.Scatter(x=years, y=profit_margin, mode='lines+markers', name="Profit Margin"), row=2, col=1)

# Custom vs Product Split
fig.add_trace(go.Scatter(x=years, y=split_ratio*100, mode='lines+markers', name="Custom %"), row=2, col=2)

fig.update_layout(
    height=700, width=1000,
    title_text="Revenue Forecast Dashboard",
    showlegend=True,
    hovermode="x unified"
)

# Show the figure
st.plotly_chart(fig, use_container_width=True)

# --- INSIGHTS SECTION ---
st.markdown("""
**Insights:**
- **Total Revenue:** Combines custom and product sales, including design services.
- **Required Volume Multiplier:** Shows how much product volume must increase to match profits if custom share decreases.
- **Profit Margin:** Illustrates overall profitability based on mix.
- **Custom vs Product Split:** Current slider mix of custom vs product homes.
""")
