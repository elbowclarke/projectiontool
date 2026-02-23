import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ------------------------
# Brand Colors
# ------------------------
ACCENT_RED = "#D71920"
TEXT_DARK = "#1A1A1A"
LIGHT_BG = "#FFFFFF"
SECONDARY_GRAY = "#4A4A4A"

# ------------------------
# App Layout
# ------------------------
st.set_page_config(layout="wide", page_title="Bensonwood Revenue & Profit Forecaster")

st.title("Bensonwood Revenue & Profit Forecaster")

# ------------------------
# Scenario Tabs
# ------------------------
saved = st.session_state.get("saved_scenarios", {})

tab_names = list(saved.keys()) + ["New Scenario"]
tabs = st.tabs(tab_names)

for idx, tab in enumerate(tabs):
    with tab:
        if tab == "New Scenario":
            # ------------------------
            # Input Sliders & Help
            # ------------------------
            left_col, center_col, right_col = st.columns([1, 2, 1])

            with left_col:
                st.header("Inputs")

                mix_custom = st.slider(
                    "Custom % of Business",
                    0, 100, 60,
                    help="Percent of revenue from custom homes vs product homes."
                )

                product_price = st.number_input(
                    "Product Home Price ($)",
                    min_value=100000, max_value=2000000,
                    step=25000, value=650000,
                    help="Average sale price for product homes."
                )

                custom_design_price = st.number_input(
                    "Custom Design Tier Price ($)",
                    min_value=5000, max_value=100000,
                    step=1000, value=45000,
                    help="Average fee for custom home design services."
                )

                product_design_price = st.number_input(
                    "Product Design Tier Price ($)",
                    min_value=5000, max_value=50000,
                    step=1000, value=18000,
                    help="Average fee for product home design services."
                )

                years = st.slider(
                    "Forecast Time Horizon (Years)",
                    min_value=1, max_value=10, value=5,
                    help="Length of the projection period."
                )

                custom_margin = st.slider(
                    "Custom Home Margin %",
                    0, 100, 25,
                    help="Profit margin on custom homes."
                )

                product_margin = st.slider(
                    "Product Home Margin %",
                    0, 100, 20,
                    help="Profit margin on product homes."
                )

                max_custom_units = st.number_input(
                    "Max Custom Units/Year",
                    min_value=0, max_value=200,
                    value=20,
                    help="Manufacturing or build capacity for custom homes."
                )

                max_product_units = st.number_input(
                    "Max Product Units/Year",
                    min_value=0, max_value=200,
                    value=15,
                    help="Manufacturing capacity for product homes."
                )

                save_name = st.text_input("Save Scenario As", "")

                if st.button("Save Scenario"):
                    saved[save_name] = {
                        "mix_custom": mix_custom,
                        "product_price": product_price,
                        "custom_design_price": custom_design_price,
                        "product_design_price": product_design_price,
                        "years": years,
                        "custom_margin": custom_margin,
                        "product_margin": product_margin,
                        "max_custom_units": max_custom_units,
                        "max_product_units": max_product_units,
                    }
                    st.session_state["saved_scenarios"] = saved
                    st.experimental_rerun()

            # ------------------------
            # Calculations
            # ------------------------
            with center_col:
                time = np.arange(1, years + 1)

                # Mix
                mix = mix_custom/100
                custom_units = np.round(mix * (max_custom_units+max_product_units) * np.ones_like(time))
                product_units = np.round((1-mix) * (max_custom_units+max_product_units) * np.ones_like(time))

                rev_custom = custom_units * (product_price + custom_design_price)
                rev_product = product_units * (product_price + product_design_price)

                total_revenue = rev_custom + rev_product

                profit_custom = rev_custom * (custom_margin/100)
                profit_product = rev_product * (product_margin/100)
                total_profit = profit_custom + profit_product

                baseline_profit = total_profit[0]

                shortfall = np.maximum(baseline_profit - total_profit, 0)
                profit_per_prod = (product_price+product_design_price)*(product_margin/100)
                volume_needed_factor = np.where(
                    profit_per_prod > 0,
                    1 + shortfall/profit_per_prod,
                    np.ones_like(time)
                )

                # ------------------------
                # Subplot Dashboard
                # ------------------------
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=[
                        "Total Revenue",
                        "Required Volume Increase",
                        "Profit Margin",
                        "Custom vs Product Mix"
                    ]
                )

                fig.add_trace(go.Scatter(
                    x=time, y=total_revenue,
                    name="Total Revenue",
                    line=dict(color=ACCENT_RED)
                ), row=1, col=1)

                fig.add_trace(go.Bar(
                    x=time, y=(volume_needed_factor-1)*100,
                    name="Extra % Volume",
                    marker_color=ACCENT_RED, opacity=0.6
                ), row=1, col=2)

                fig.add_trace(go.Scatter(
                    x=time, y=(total_profit/total_revenue),
                    name="Profit Margin %",
                    line=dict(color=TEXT_DARK)
                ), row=2, col=1)

                fig.add_trace(go.Scatter(
                    x=time, y=mix*100*np.ones_like(time),
                    name="Custom %",
                    line=dict(color=SECONDARY_GRAY)
                ), row=2, col=2)

                fig.update_layout(
                    height=700, width=920,
                    title_text="Revenue & Volume Forecast",
                    plot_bgcolor=LIGHT_BG
                )

                st.plotly_chart(fig, use_container_width=True)

            # ------------------------
            # Executive Insights
            # ------------------------
            with right_col:
                st.header("Executive Insights")
                st.markdown(f"**Scenario:** Custom {mix_custom}%, Product {100-mix_custom}%")
                st.markdown(f"**Year 1 Profit:** ${total_profit[0]:,.0f}")
                st.markdown(f"**Year {years} Profit:** ${total_profit[-1]:,.0f}")
                if shortfall[-1] > 0:
                    st.error(
                        f"By Year {years}, profit declines by ${shortfall[-1]:,.0f} "
                        "– requires significant volume increase to break even."
                    )
                else:
                    st.success("Profit maintained or improved over horizon.")

        else:
            st.write(f"### Saved Scenario: {tab}")
            sc = saved[tab]
            st.json(sc)
