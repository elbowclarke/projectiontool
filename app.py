import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Bensonwood Strategic Forecaster", layout="wide")

# --- Logo ---
st.markdown("""
<div style="text-align:center; margin-bottom: 20px;">
<img src="https://bensonwood.com/wp-content/uploads/2021/10/bensonwood-logo-wht.svg" width="250">
</div>
""", unsafe_allow_html=True)

st.title("Strategic Revenue & Profit Transition Model")

# ---------------- SIDEBAR ---------------- #

st.sidebar.header("Scenario Inputs")

years = st.sidebar.slider(
    "Planning Horizon (Years)",
    5, 15, 10,
    help="Number of years over which the transition occurs."
)

baseline_revenue = st.sidebar.number_input(
    "Current Annual Revenue ($M)",
    1.0, 200.0, 10.0, 0.5,
    help="Current total company revenue."
)

annual_growth = st.sidebar.slider(
    "Annual Revenue Growth Rate %",
    0, 25, 8,
    help="Annual top-line growth assumption."
)

start_custom = st.sidebar.slider(
    "Starting Custom Mix %",
    50, 80, 60,
    help="Current % of revenue from custom work."
)

target_custom = st.sidebar.slider(
    "Target Custom Mix %",
    40, 70, 50,
    help="Target % of revenue from custom work at end of horizon."
)

custom_margin = st.sidebar.slider(
    "Custom Work Margin %",
    15, 35, 25,
    help="Average margin earned on custom projects."
)

product_margin = st.sidebar.slider(
    "Product Work Margin %",
    10, 25, 18,
    help="Average margin earned on product work."
)

benchmark_margin = st.sidebar.slider(
    "Benchmark Margin %",
    15, 30, 25,
    help="Minimum acceptable blended company margin."
)

# ---------------- CALCULATIONS ---------------- #

def project(revenue, growth, years):
    return [revenue * ((1 + growth/100) ** i) for i in range(years)]

revenues = project(baseline_revenue, annual_growth, years)

df = pd.DataFrame(index=range(1, years+1))
df["Revenue"] = revenues

# Baseline: fixed starting mix
df["Baseline_CustomMix"] = start_custom
df["Baseline_ProductMix"] = 100 - start_custom

df["Baseline_Profit"] = (
    df["Revenue"] *
    ((start_custom/100)*custom_margin +
     ((100-start_custom)/100)*product_margin) / 100
)

# Transition mix
df["Transition_CustomMix"] = np.linspace(start_custom, target_custom, years)
df["Transition_ProductMix"] = 100 - df["Transition_CustomMix"]

df["Transition_Profit"] = (
    df["Revenue"] *
    ((df["Transition_CustomMix"]/100)*custom_margin +
     (df["Transition_ProductMix"]/100)*product_margin) / 100
)

# Required product revenue to match baseline profit
required_product_revenue = []

for i in range(years):
    revenue = df["Revenue"].iloc[i]
    custom_mix = df["Transition_CustomMix"].iloc[i] / 100

    custom_profit = revenue * custom_mix * custom_margin / 100
    baseline_profit = df["Baseline_Profit"].iloc[i]

    remaining_profit_needed = baseline_profit - custom_profit

    if product_margin > 0:
        required_product = remaining_profit_needed / (product_margin / 100)
    else:
        required_product = 0

    actual_product_revenue = revenue * (1 - custom_mix)
    additional_needed = max(0, required_product - actual_product_revenue)

    required_product_revenue.append(additional_needed)

df["Additional_Product_Revenue_Required"] = required_product_revenue

# Cumulative profit
df["Baseline_Cumulative"] = df["Baseline_Profit"].cumsum()
df["Transition_Cumulative"] = df["Transition_Profit"].cumsum()

# Crossover detection
crossover_year = None
for i in range(years):
    if df["Transition_Cumulative"].iloc[i] >= df["Baseline_Cumulative"].iloc[i]:
        crossover_year = i + 1
        break

# ---------------- LAYOUT ---------------- #

col1, col2, col3 = st.columns([1,2,1])

# ----- LEFT: Key Metrics ----- #
with col1:
    st.subheader("Required Volume Impact")

    max_required = df["Additional_Product_Revenue_Required"].max()

    st.metric(
        "Max Additional Product Revenue Required",
        f"${max_required:.1f}M"
    )

    if max_required > 0:
        peak_year = df["Additional_Product_Revenue_Required"].idxmax()
        st.write(f"Peak pressure occurs in Year {peak_year}")
    else:
        st.write("Transition maintains baseline profit without additional volume.")

# ----- CENTER: Cumulative Profit Chart ----- #
with col2:

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Baseline_Cumulative"],
        name="Baseline Cumulative Profit",
        mode="lines",
        line=dict(width=3)
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Transition_Cumulative"],
        name="Transition Cumulative Profit",
        mode="lines",
        line=dict(width=3, dash="dash")
    ))

    if crossover_year:
        fig.add_vline(
            x=crossover_year,
            line_dash="dot"
        )

    fig.update_layout(
        title="Cumulative Profit Comparison",
        xaxis_title="Year",
        yaxis_title="Cumulative Profit ($M)",
        template="plotly_white",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

# ----- RIGHT: Executive Summary ----- #
with col3:
    st.subheader("Executive Summary")

    total_baseline = df["Baseline_Cumulative"].iloc[-1]
    total_transition = df["Transition_Cumulative"].iloc[-1]

    st.write(f"Baseline 10Y Profit: ${total_baseline:.1f}M")
    st.write(f"Transition 10Y Profit: ${total_transition:.1f}M")

    diff = total_transition - total_baseline

    if diff > 0:
        st.success(f"Transition Outperforms by ${diff:.1f}M")
    else:
        st.error(f"Transition Underperforms by ${abs(diff):.1f}M")

    if crossover_year:
        st.write(f"Crossover Year: Year {crossover_year}")
    else:
        st.write("No crossover within selected horizon.")
