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
st.markdown("Model the revenue and profit implications of shifting from custom work toward product-based work.")

# --- Sidebar ---
st.sidebar.header("Scenario Inputs")

years = st.sidebar.slider(
    "Planning Horizon (Years)",
    5, 15, 10, 1,
    help="Select how many years the transition from custom-heavy to product-heavy mix should take."
)

base_custom_mix = st.sidebar.slider(
    "Starting Custom Work %",
    50, 80, 60, 1,
    help="Percentage of revenue currently derived from custom project work."
)

target_custom_mix = st.sidebar.slider(
    "Target Custom Work %",
    40, 70, 50, 1,
    help="Desired percentage of revenue from custom work at the end of the planning horizon."
)

baseline_revenue = st.sidebar.number_input(
    "Current Annual Revenue ($M)",
    1.0, 100.0, 10.0, 0.1,
    help="Total company revenue in millions for the current year."
)

custom_margin = st.sidebar.slider(
    "Custom Work Margin %",
    15, 35, 25, 1,
    help="Average gross or contribution margin earned on custom project work."
)

product_margin = st.sidebar.slider(
    "Product Work Margin %",
    10, 25, 18, 1,
    help="Average gross or contribution margin earned on product-based work."
)

annual_growth_rate = st.sidebar.slider(
    "Annual Revenue Growth Rate %",
    0, 25, 8, 1,
    help="Overall annual revenue growth assumption before mix effects."
)

benchmark_margin = st.sidebar.slider(
    "Benchmark Profit Margin %",
    15, 30, 25, 1,
    help="Target or minimum acceptable blended company profit margin."
)

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
    custom_margin,
    product_margin
)

below_benchmark = scenario[scenario['ProfitMargin'] < benchmark_margin]

# --- Layout ---
col1, col2, col3 = st.columns([1, 2, 1])

# --- Left Column ---
with col1:
    st.markdown("### Scenario Summary")
    st.write(f"Transition over {years} years.")
    st.write(f"Revenue grows from ${baseline_revenue:.1f}M to ${scenario['Revenue'].iloc[-1]:.1f}M.")
    st.write(f"Custom mix shifts from {base_custom_mix}% to {target_custom_mix}%.")

# --- Center Chart ---
with col2:
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=scenario.index,
        y=scenario['CustomRevenue'],
        name='Custom Revenue',
        hovertemplate='Year %{x}<br>Custom Revenue: $%{y:.1f}M'
    ))

    fig.add_trace(go.Bar(
        x=scenario.index,
        y=scenario['ProductRevenue'],
        name='Product Revenue',
        hovertemplate='Year %{x}<br>Product Revenue: $%{y:.1f}M'
    ))

    fig.add_trace(go.Scatter(
        x=scenario.index,
        y=scenario['ProfitMargin'],
        name='Profit Margin %',
        mode='lines+markers',
        yaxis='y2',
        line=dict(width=3),
        hovertemplate='Year %{x}<br>Blended Margin: %{y:.1f}%'
    ))

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
        title="Revenue Mix & Profit Margin Projection",
        xaxis_title="Year",
        yaxis=dict(title="Revenue ($M)"),
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
    - Ending Revenue: **${scenario['Revenue'].iloc[-1]:.1f}M**
    - Ending Profit Margin: **{scenario['ProfitMargin'].iloc[-1]:.1f}%**
    - Ending Profit: **${scenario['Profit'].iloc[-1]:.1f}M**
    - Benchmark Margin: **{benchmark_margin}%**
    """)

    if not below_benchmark.empty:
        years_list = ", ".join([f"Year {y}" for y in below_benchmark.index])
        st.error(f"Margin falls below benchmark in: {years_list}")
    else:
        st.success("Margin remains at or above benchmark across all years.")
