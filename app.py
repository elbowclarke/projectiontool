import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Bensonwood Revenue Forecaster", layout="wide")

# ----------------------------
# Logo
# ----------------------------
st.markdown("""
<div style="text-align:center; margin-bottom: 20px;">
<img src="https://bensonwood.com/wp-content/uploads/2021/10/bensonwood-logo-wht.svg" width="250">
</div>
""", unsafe_allow_html=True)

st.title("Revenue & Product Mix Forecaster")

# ----------------------------
# Sidebar Inputs
# ----------------------------
st.sidebar.header("Scenario Inputs")

years = st.sidebar.slider(
    "Planning Horizon (Years)", 5, 15, 10, 1,
    help="Number of years over which the mix transition occurs."
)

base_custom_mix = st.sidebar.slider(
    "Starting Custom Work %", 50, 80, 60, 1,
    help="Current percentage of revenue from custom work."
)

target_custom_mix = st.sidebar.slider(
    "Target Custom Work %", 40, 70, 50, 1,
    help="Desired custom revenue percentage at end of horizon."
)

baseline_revenue = st.sidebar.number_input(
    "Current Annual Revenue ($M)", 1.0, 100.0, 10.0, 0.1
)

custom_margin = st.sidebar.slider(
    "Custom Work Margin %", 15, 35, 25, 1,
    help="Average gross or contribution margin on custom work."
)

product_margin = st.sidebar.slider(
    "Product Work Margin %", 10, 25, 18, 1,
    help="Average gross or contribution margin on product work."
)

annual_growth_rate = st.sidebar.slider(
    "Annual Revenue Growth Rate %", 0, 25, 8, 1
)

benchmark_margin = st.sidebar.slider(
    "Benchmark Profit Margin %", 15, 30, 25, 1
)

# ----------------------------
# Projection Functions
# ----------------------------
def project_mix(years, revenue, growth, base_mix, target_mix, custom_margin, product_margin):
    df = pd.DataFrame(index=range(1, years + 1))
    df['Revenue'] = revenue * ((1 + growth/100) ** (df.index - 1))
    df['CustomMix'] = np.linspace(base_mix, target_mix, years)
    df['ProductMix'] = 100 - df['CustomMix']
    df['CustomRevenue'] = df['Revenue'] * df['CustomMix'] / 100
    df['ProductRevenue'] = df['Revenue'] * df['ProductMix'] / 100
    df['Profit'] = (
        df['CustomRevenue'] * custom_margin +
        df['ProductRevenue'] * product_margin
    ) / 100
    df['ProfitMargin'] = df['Profit'] / df['Revenue'] * 100
    return df

def baseline_projection(years, revenue, growth, custom_mix, custom_margin, product_margin):
    df = pd.DataFrame(index=range(1, years + 1))
    df['Revenue'] = revenue * ((1 + growth/100) ** (df.index - 1))
    product_mix = 100 - custom_mix
    df['Profit'] = (
        df['Revenue'] * custom_mix/100 * custom_margin +
        df['Revenue'] * product_mix/100 * product_margin
    ) / 100
    return df

transition = project_mix(
    years, baseline_revenue, annual_growth_rate,
    base_custom_mix, target_custom_mix,
    custom_margin, product_margin
)

baseline = baseline_projection(
    years, baseline_revenue, annual_growth_rate,
    base_custom_mix,
    custom_margin, product_margin
)

# ----------------------------
# FIRST CHART (Existing)
# ----------------------------
fig1 = go.Figure()

fig1.add_trace(go.Bar(
    x=transition.index,
    y=transition['CustomRevenue'],
    name='Custom Revenue'
))

fig1.add_trace(go.Bar(
    x=transition.index,
    y=transition['ProductRevenue'],
    name='Product Revenue'
))

fig1.add_trace(go.Scatter(
    x=transition.index,
    y=transition['ProfitMargin'],
    name='Profit Margin %',
    yaxis='y2',
    mode='lines+markers'
))

fig1.add_trace(go.Scatter(
    x=transition.index,
    y=[benchmark_margin]*years,
    name='Benchmark Margin',
    yaxis='y2',
    mode='lines',
    line=dict(dash='dash')
))

fig1.update_layout(
    title="Revenue Mix & Profit Margin",
    barmode='stack',
    yaxis=dict(title="Revenue ($M)"),
    yaxis2=dict(
        title="Profit Margin (%)",
        overlaying='y',
        side='right',
        range=[15, 30]
    ),
    height=600
)

st.plotly_chart(fig1, use_container_width=True)

# ==========================================================
# SECOND EXECUTIVE DIAGRAM
# ==========================================================

st.markdown("---")
st.subheader("Strategic Impact Analysis")

# Required Product Revenue to Maintain Baseline Profit
required_product_revenue = (
    (baseline['Profit'] * 100 -
     transition['CustomRevenue'] * custom_margin)
    / product_margin
)

additional_product_needed = required_product_revenue - transition['ProductRevenue']

# Cumulative Profit
transition['CumulativeProfit'] = transition['Profit'].cumsum()
baseline['CumulativeProfit'] = baseline['Profit'].cumsum()

# Crossover Detection
crossover_year = None
for year in transition.index:
    if transition.loc[year, 'CumulativeProfit'] >= baseline.loc[year, 'CumulativeProfit']:
        crossover_year = year
        break

fig2 = go.Figure()

# Cumulative Profit Lines
fig2.add_trace(go.Scatter(
    x=transition.index,
    y=transition['CumulativeProfit'],
    name='Transition Cumulative Profit',
    mode='lines+markers'
))

fig2.add_trace(go.Scatter(
    x=baseline.index,
    y=baseline['CumulativeProfit'],
    name='Baseline Cumulative Profit',
    mode='lines+markers',
    line=dict(dash='dash')
))

# Required Additional Product Revenue Bars
fig2.add_trace(go.Bar(
    x=transition.index,
    y=additional_product_needed,
    name='Additional Product Revenue Required ($M)',
    yaxis='y2',
    opacity=0.4
))

# Mark Crossover Year
if crossover_year:
    fig2.add_vline(
        x=crossover_year,
        line_dash="dot",
        annotation_text=f"Crossover Year {crossover_year}",
        annotation_position="top"
    )

fig2.update_layout(
    title="Cumulative Profit & Required Product Volume",
    yaxis=dict(title="Cumulative Profit ($M)"),
    yaxis2=dict(
        title="Additional Product Revenue Needed ($M)",
        overlaying='y',
        side='right'
    ),
    height=600
)

st.plotly_chart(fig2, use_container_width=True)

# ----------------------------
# Executive Summary
# ----------------------------
st.markdown("### Executive Summary")

colA, colB, colC = st.columns(3)

with colA:
    st.metric("Year 10 Transition Profit ($M)", f"{transition['Profit'].iloc[-1]:.2f}")

with colB:
    st.metric("Year 10 Baseline Profit ($M)", f"{baseline['Profit'].iloc[-1]:.2f}")

with colC:
    if crossover_year:
        st.success(f"Crossover occurs in Year {crossover_year}")
    else:
        st.error("No crossover within planning horizon")
