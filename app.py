import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Bensonwood Revenue Forecaster", layout="wide")

# --- Logo ---
st.markdown("""
<div style="text-align:center; margin-bottom: 20px;">
<img src="https://bensonwood.com/wp-content/uploads/2021/10/bensonwood-logo-wht.svg" width="250">
</div>
""", unsafe_allow_html=True)

st.title("Revenue & Product Mix Forecaster")
st.markdown("Visualize 10-year growth and profit impact when shifting from custom-heavy work to more product-focused work.")

# --- Sidebar ---
st.sidebar.header("Scenario Inputs")

years = 10
base_custom_mix = st.sidebar.slider("Baseline Custom Work %", 50, 80, 60, 1)
target_custom_mix = st.sidebar.slider("Target Custom Work %", 40, 70, 50, 1)
baseline_revenue = st.sidebar.number_input("Current Annual Revenue ($M)", 1.0, 100.0, 10.0, 0.1)
baseline_profit_margin = st.sidebar.slider("Custom Work Margin %", 15, 35, 25, 1)
product_margin = st.sidebar.slider("Product Work Margin %", 10, 25, 18, 1)
annual_growth_rate = st.sidebar.slider("Annual Revenue Growth Rate %", 0, 25, 8, 1)

benchmark_margin = st.sidebar.slider("Benchmark Profit Margin %", 15, 30, 25, 1)

# --- Projection Function ---
def project_mix(years, revenue, growth, base_mix, target_mix, custom_margin, product_margin):
    df = pd.DataFrame(index=range(1, years + 1))
    df['Revenue'] = revenue * ((1 + growth/100) ** (df.index - 1))

    df['CustomMix'] = np.linspace(base_mix, target_mix, years)
    df['ProductMix'] = 100 - df['CustomMix']

    df['CustomRevenue'] = df['Revenue'] * df['CustomMix'] / 100
    df['ProductRevenue'] = df['Revenue'] * df['ProductMix'] / 100

    df['ProfitMargin'] = (
        (df['CustomRevenue'] * custom_margin +
         df['ProductRevenue'] * product_margin)
        / df['Revenue']
    )

    df['Profit'] = df['Revenue'] * df['ProfitMargin'] / 100

    return df

scenario = project_mix(
    years,
    baseline_revenue,
    annual_growth_rate,
    base_custom_mix,
    target_custom_mix,
    baseline_profit_margin,
    product_margin
)

# Identify below-benchmark years
below_benchmark = scenario[scenario['ProfitMargin'] < benchmark_margin]

# --- Layout ---
col1, col2, col3 = st.columns([1, 2, 1])

# --- Left Column ---
with col1:
    st.markdown("### Scenario Summary")
    st.write(f"Shift from {base_custom_mix}% custom to {target_custom_mix}% custom over {years} years.")
    st.write(f"Revenue grows from ${baseline_revenue:.1f}M to ${scenario['Revenue'].iloc[-1]:.1f}M.")

# --- Center Chart ---
with col2:
    fig = go.Figure()

    # Stacked revenue bars
    fig.add_trace(go.Bar(
        x=scenario.index,
        y=scenario['CustomRevenue'],
        name='Custom Revenue',
        hovertemplate='Year %{x}<br>Custom: $%{y:.1f}M'
    ))

    fig.add_trace(go.Bar(
        x=scenario.index,
        y=scenario['ProductRevenue'],
        name='Product Revenue',
        hovertemplate='Year %{x}<br>Product: $%{y:.1f}M'
    ))

    # Profit margin line
    fig.add_trace(go.Scatter(
        x=scenario.index,
        y=scenario['ProfitMargin'],
        name='Profit Margin %',
        mode='lines+markers',
        yaxis='y2',
        line=dict(width=3),
        hovertemplate='Year %{x}<br>Margin: %{y:.1f}%'
    ))

    # Highlight below-benchmark years
    if not below_benchmark.empty:
        fig.add_trace(go.Scatter(
            x=below_benchmark.index,
            y=below_benchmark['ProfitMargin'],
            name='Below Benchmark',
            mode='markers',
            marker=dict(size=10, color='red'),
            yaxis='y2',
            hovertemplate='Year %{x}<br>Below Benchmark: %{y:.1f}%'
        ))

    # Benchmark horizontal line
    fig.add_trace(go.Scatter(
        x=scenario.index,
        y=[benchmark_margin] * len(scenario.index),
        name='Benchmark Margin',
        mode='lines',
        yaxis='y2',
        line=dict(dash='dash'),
        hovertemplate='Benchmark: %{y:.1f}%'
    ))

    fig.update_layout(
        title="Revenue Mix & Profit Margin (10-Year Projection)",
        xaxis_title="Year",
        yaxis=dict(
            title="Revenue ($M)",
            side='left'
        ),
        yaxis2=dict(
            title="Profit Margin (%)",
            overlaying='y',
            side='right',
            range=[15, 30],
            showgrid=False
        ),
        barmode='stack',
        template="plotly_white",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

# --- Executive Insights ---
with col3:
    st.header("Executive Insights")
    st.markdown(f"""
    - Ending revenue: **${scenario['Revenue'].iloc[-1]:.1f}M**
    - Ending profit margin: **{scenario['ProfitMargin'].iloc[-1]:.1f}%**
    - Ending profit: **${scenario['Profit'].iloc[-1]:.1f}M**
    - Benchmark margin: **{benchmark_margin}%**
    """)

    if not below_benchmark.empty:
        years_list = ", ".join([f"Year {y}" for y in below_benchmark.index])
        st.error(f"Margin falls below benchmark in: {years_list}")
    else:
        st.success("Margin stays at or above benchmark across all years.")
