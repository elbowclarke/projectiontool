import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Must be first Streamlit command
st.set_page_config(page_title="Bensonwood Revenue Forecast", layout="wide")

# =======================
# STYLE
# =======================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

:root {
    --bw-bg: #1d2f2b;        /* lighter green background */
    --bw-panel: #162321;
    --bw-panel-2: #1d2f2b;
    --bw-border: #2d4540;
    --bw-text: #e7efec;
    --bw-forest: #2f5a51;
    --bw-wood: #b88152;
}

html, body, .stApp {
    font-family: 'Montserrat', sans-serif;
    color: var(--bw-text) !important;
    background: var(--bw-bg) !important;
}

.block-container {
    background: var(--bw-panel);
    border: 1px solid var(--bw-border);
    border-radius: 12px;
    padding: 1.5rem;
}

section[data-testid="stSidebar"] {
    background: var(--bw-panel-2);
    border-right: 1px solid var(--bw-border);
}

h1, h2, h3, h4, p, li, label, span, div {
    color: var(--bw-text) !important;
}

/* Tabs */
[data-baseweb="tab"] {
    background: transparent !important;
    border: 1px solid var(--bw-border);
    color: var(--bw-text) !important;
    font-weight: 600;
}

[aria-selected="true"][data-baseweb="tab"] {
    background: var(--bw-forest) !important;
    color: #ffffff !important;
}

/* Slider styling */
[data-baseweb="slider"] [role="slider"] {
    background-color: #ffffff !important;
    border-color: #ffffff !important;
}

[data-baseweb="slider"] [data-testid="stTickBarMin"],
[data-baseweb="slider"] [data-testid="stTickBarMax"],
[data-baseweb="slider"] [data-baseweb="typography"] {
    background: transparent !important;
    color: #ffffff !important;
}

/* Tooltip */
[data-baseweb="tooltip"],
[role="tooltip"] {
    background-color: rgba(0,0,0,0.65) !important;
    color: #ffffff !important;
    border: 1px solid var(--bw-border) !important;
}

/* Number inputs */
input[type="number"] {
    background: transparent !important;
    color: #ffffff !important;
    border: 1px solid var(--bw-border) !important;
}

/* Streamlit top header */
header[data-testid="stHeader"] {
    background-color: #1d2f2b !important;  /* match lighter green */
}

/* Remove shadow line under header */
header[data-testid="stHeader"] > div {
    box-shadow: none !important;
}

/* Add spacing below header */
.block-container {
    padding-top: 2rem !important;
}

</style>
""", unsafe_allow_html=True)

# =======================
# HEADER (Logo left biased)
# =======================

LOGO_URL = "https://bensonwood.com/wp-content/uploads/2021/10/bensonwood-logo-wht.svg"

st.markdown(
    f"<img src='{LOGO_URL}' width='260' style='margin-bottom:10px;'>",
    unsafe_allow_html=True
)

st.title("Revenue & Product Mix Forecast")
st.markdown("Model the revenue and profit implications of shifting from custom work toward product-based work.")

# =======================
# SIDEBAR INPUTS
# =======================

st.sidebar.header("Scenario Inputs")

# Financial Baseline
baseline_revenue = st.sidebar.number_input("Current Annual Revenue ($M)", 1.0, 100.0, 32.5, 0.1)
benchmark_margin = st.sidebar.slider("Benchmark Profit Margin %", 15, 30, 21, 1)
custom_margin = st.sidebar.slider("Custom Work Margin %", 15, 35, 25, 1)
product_margin = st.sidebar.slider("Product Work Margin %", 10, 25, 18, 1)
annual_growth_rate = st.sidebar.slider("Annual Revenue Growth Rate %", 0, 25, 8, 1)

st.sidebar.markdown("---")
st.sidebar.subheader("Transition Projection")

years = st.sidebar.slider("Planning Horizon (Years)", 5, 15, 10, 1)
base_custom_mix = st.sidebar.slider("Starting Custom Work %", 50, 80, 60, 1)
target_custom_mix = st.sidebar.slider("Target Custom Work %", 40, 70, 50, 1)

# =======================
# MODEL
# =======================

def project_mix(years, revenue, growth, base_mix, target_mix, custom_margin, product_margin):
    df = pd.DataFrame(index=range(1, years + 1))
    df["Revenue"] = revenue * ((1 + growth / 100) ** (df.index - 1))
    df["CustomMix"] = np.linspace(base_mix, target_mix, years)
    df["ProductMix"] = 100 - df["CustomMix"]
    df["CustomRevenue"] = df["Revenue"] * df["CustomMix"] / 100
    df["ProductRevenue"] = df["Revenue"] * df["ProductMix"] / 100

    df["ProfitMargin"] = (
        (df["CustomRevenue"] * custom_margin + df["ProductRevenue"] * product_margin)
        / df["Revenue"]
    )

    df["Profit"] = df["Revenue"] * df["ProfitMargin"] / 100
    return df

scenario = project_mix(
    years, baseline_revenue, annual_growth_rate,
    base_custom_mix, target_custom_mix,
    custom_margin, product_margin
)

baseline_scenario = project_mix(
    years, baseline_revenue, annual_growth_rate,
    base_custom_mix, base_custom_mix,
    custom_margin, product_margin
)

scenario["CumulativeProfit"] = scenario["Profit"].cumsum()
baseline_scenario["CumulativeProfit"] = baseline_scenario["Profit"].cumsum()

below_benchmark = scenario[scenario["ProfitMargin"] < benchmark_margin]

# =======================
# LAYOUT
# =======================

col1, col2, col3 = st.columns([1,2,1])

with col1:
    st.markdown("### Scenario Summary")
    st.markdown(f"- Transition over {years} years")
    st.markdown(f"- Revenue grows to ${scenario['Revenue'].iloc[-1]:.1f}M")
    st.markdown(f"- Custom mix shifts from {base_custom_mix}% to {target_custom_mix}%")

with col2:
    fig = go.Figure()
    fig.add_bar(x=scenario.index, y=scenario["CustomRevenue"], name="Custom Revenue")
    fig.add_bar(x=scenario.index, y=scenario["ProductRevenue"], name="Product Revenue")

    fig.add_trace(go.Scatter(
        x=scenario.index,
        y=scenario["ProfitMargin"],
        name="Profit Margin %",
        yaxis="y2",
        mode="lines+markers"
    ))

    fig.update_layout(
        barmode="stack",
        yaxis=dict(title="Revenue ($M)"),
        yaxis2=dict(
            title="Profit Margin %",
            overlaying="y",
            side="right",
            range=[15,30]
        ),
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

with col3:
    st.header("Executive Insights")
    st.markdown(f"- Ending Revenue: **${scenario['Revenue'].iloc[-1]:.1f}M**")
    st.markdown(f"- Ending Profit Margin: **{scenario['ProfitMargin'].iloc[-1]:.1f}%**")
    st.markdown(f"- Ending Profit: **${scenario['Profit'].iloc[-1]:.1f}M**")

    if not below_benchmark.empty:
        years_list = ", ".join([f"Year {y}" for y in below_benchmark.index])
        st.markdown(f"**Margin below benchmark in:** {years_list}")
    else:
        st.markdown("Margin remains at or above benchmark.")

