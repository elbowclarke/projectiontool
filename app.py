import os
from io import BytesIO

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# IMPORTANT:
# - Must be the first Streamlit call in the file
# - Must appear only once in the entire app page
st.set_page_config(page_title="Bensonwood Revenue Forecaster", layout="wide")

# --- Theme + Branding ---
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

        :root {
            --bw-bg: #0f1716;
            --bw-panel: #162321;
            --bw-panel-2: #1d2f2b;
            --bw-border: #2d4540;
            --bw-text: #e7efec;
            --bw-muted-text: #b9cbc5;
            --bw-forest: #2f5a51;
            --bw-sage: #7f9b90;
            --bw-wood: #b88152;
        }

        html, body, [class*="css"], .stApp {
            font-family: 'Montserrat', sans-serif;
            color: var(--bw-text) !important;
            background: var(--bw-bg) !important;
        }

        .block-container {
            background: var(--bw-panel);
            border: 1px solid var(--bw-border);
            border-radius: 12px;
            padding: 1.25rem 1.5rem 1.75rem;
        }

        h1, h2, h3, h4, p, li, label, span, div {
            color: var(--bw-text) !important;
        }

        h1, h2, h3 {
            letter-spacing: 0.2px;
        }

        section[data-testid="stSidebar"] {
            background: var(--bw-panel-2);
            border-right: 1px solid var(--bw-border);
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div {
            color: var(--bw-text) !important;
        }

        .stMarkdown p, .stMarkdown li, .stAlert, .stCaption,
        .stRadio label, .stRadio div, .stSelectbox label, .stNumberInput label, .stSlider label,
        [data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {
            color: var(--bw-text) !important;
        }

        [data-baseweb="tab-list"] { gap: 0.3rem; }

        [data-baseweb="tab"] {
            background-color: #223531;
            border-radius: 0.4rem 0.4rem 0 0;
            border: 1px solid var(--bw-border);
            color: var(--bw-text) !important;
            font-weight: 600;
            padding: 0.6rem 0.9rem;
        }

        [aria-selected="true"][data-baseweb="tab"] {
            background-color: var(--bw-forest);
            color: #ffffff !important;
        }

        .stAlert {
            border-radius: 10px;
            border: 1px solid var(--bw-border) !important;
            background-color: #202a2c !important;
        }

        [data-baseweb="notification"] {
            border: 1px solid var(--bw-border) !important;
            background-color: #202a2c !important;
        }

        [data-baseweb="notification"] * { color: var(--bw-text) !important; }

        .stAlert [data-testid="stMarkdownContainer"] p { color: var(--bw-text) !important; }

        [data-baseweb="slider"] [role="slider"] {
            background-color: #ffffff !important;
            border-color: #ffffff !important;
        }

        [data-baseweb="slider"] [data-testid="stTickBarMin"],
        [data-baseweb="slider"] [data-testid="stTickBarMax"] {
            background-color: #ffffff !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Revenue & Product Mix Forecaster")
st.markdown("Model the revenue and profit implications of shifting from custom work toward product-based work.")

# --- Sidebar ---
# Use remote logo to avoid missing local file crashes (the issue in your logs)
LOGO_URL = "https://bensonwood.com/wp-content/uploads/2021/10/bensonwood-logo-wht.svg"
st.sidebar.image(LOGO_URL, use_container_width=True)

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
    1.0, 100.0, 32.5, 0.1,
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
    15, 30, 21, 1,
    help="Target or minimum acceptable blended company profit margin."
)


# --- Projection Function ---
def project_mix(years, revenue, growth, base_mix, target_mix, custom_margin, product_margin):
    df = pd.DataFrame(index=range(1, years + 1))
    df["Revenue"] = revenue * ((1 + growth / 100) ** (df.index - 1))

    df["CustomMix"] = np.linspace(base_mix, target_mix, years)
    df["ProductMix"] = 100 - df["CustomMix"]

    df["CustomRevenue"] = df["Revenue"] * df["CustomMix"] / 100
    df["ProductRevenue"] = df["Revenue"] * df["ProductMix"] / 100

    # ProfitMargin is in percent units (e.g., 21.0 means 21%)
    df["ProfitMargin"] = (
        (df["CustomRevenue"] * custom_margin + df["ProductRevenue"] * product_margin)
        / df["Revenue"]
    )

    # Profit = Revenue * (ProfitMargin/100)
    df["Profit"] = df["Revenue"] * df["ProfitMargin"] / 100
    return df


def apply_bensonwood_figure_style(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#162321",
        font=dict(family="Montserrat, sans-serif", color="#e7efec"),
        colorway=["#2f5a51", "#b88152", "#7f9b90", "#1f3a36"],
        legend=dict(
            bgcolor="rgba(22,35,33,0.85)",
            bordercolor="#2d4540",
            borderwidth=1,
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
        ),
        margin=dict(b=120),
    )
    fig.update_xaxes(gridcolor="#2d4540", zerolinecolor="#2d4540")
    fig.update_yaxes(gridcolor="#2d4540", zerolinecolor="#2d4540")


scenario = project_mix(
    years,
    baseline_revenue,
    annual_growth_rate,
    base_custom_mix,
    target_custom_mix,
    custom_margin,
    product_margin,
)

baseline_scenario = project_mix(
    years,
    baseline_revenue,
    annual_growth_rate,
    base_custom_mix,
    base_custom_mix,
    custom_margin,
    product_margin,
)

scenario["CumulativeProfit"] = scenario["Profit"].cumsum()
baseline_scenario["CumulativeProfit"] = baseline_scenario["Profit"].cumsum()

required_profit = scenario["Revenue"] * benchmark_margin / 100
custom_profit = scenario["CustomRevenue"] * custom_margin / 100
if product_margin > 0:
    scenario["RequiredProductRevenueAtBenchmark"] = np.maximum(
        0,
        (required_profit - custom_profit) / (product_margin / 100),
    )
else:
    scenario["RequiredProductRevenueAtBenchmark"] = np.nan

scenario["RequiredProductMixAtBenchmark"] = (
    scenario["RequiredProductRevenueAtBenchmark"] / scenario["Revenue"] * 100
).clip(0, 100)

crossover_candidates = scenario[
    scenario["CumulativeProfit"] >= baseline_scenario["CumulativeProfit"]
]
crossover_year = int(crossover_candidates.index[0]) if not crossover_candidates.empty else None

below_benchmark = scenario[scenario["ProfitMargin"] < benchmark_margin]

# --- Layout ---
col1, col2, col3 = st.columns([1, 2, 1])

chart_options = [
    "Revenue Mix & Margin",
    "Required Product Volume",
    "Baseline vs Transition",
    "Cumulative Profit Crossover",
]
selected_chart = col2.radio(
    "Chart Tabs",
    chart_options,
    horizontal=True,
    label_visibility="collapsed",
)

chart_guides = {
    "Revenue Mix & Margin": """
**Revenue Mix & Margin**
- We can see how our total revenue is split between custom and product work each year.
- We can track the blended margin line to understand when our profitability improves or slips.
- We can spot benchmark risk immediately by watching red points where margin falls below target.
""",
    "Required Product Volume": """
**Required Product Volume to Maintain Benchmark Profit**
- We compare our projected product revenue against the product revenue required to hold our benchmark margin.
- If the required line runs above our projected bars, we need a plan for more volume, pricing improvements, and/or cost reductions.
- We can use this chart as an operating target because it translates a margin goal into concrete dollar volume.
""",
    "Baseline vs Transition": """
**Baseline vs Transition Cumulative Comparison**
- We compare the total profit we accumulate over time under two paths: no mix change versus transition to target mix.
- We can judge strategy durability by focusing on cumulative outcome, not single-year volatility.
- A widening spread tells us which path is compounding value faster across the full horizon.
""",
    "Cumulative Profit Crossover": """
**Cumulative Profit Curve with Crossover Year**
- We track the running cumulative profit difference between the transition path and the baseline path.
- Values above zero mean our transition has produced more total profit than baseline to date.
- The crossover marker identifies the first year the transition path pulls ahead cumulatively.
""",
}

# --- Left Column ---
with col1:
    st.markdown("### Scenario Summary")
    st.markdown(f"- Transition over {years} years.")
    st.markdown(f"- Revenue grows from ${baseline_revenue:.1f}M to ${scenario['Revenue'].iloc[-1]:.1f}M.")
    st.markdown(f"- Custom mix shifts from {base_custom_mix}% to {target_custom_mix}%.")

    st.markdown("### Chart Guide")
    st.markdown(chart_guides[selected_chart])

# --- Center Chart ---
with col2:
    if selected_chart == "Revenue Mix & Margin":
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=scenario.index,
            y=scenario["CustomRevenue"],
            name="Custom Revenue",
            marker_color="#2f5a51",
            customdata=np.stack([scenario["CustomMix"], scenario["Revenue"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Custom Revenue: $%{y:.2f}M<br>"
                "Custom Mix: %{customdata[0]:.1f}%<br>"
                "Total Revenue: $%{customdata[1]:.2f}M"
                "<extra></extra>"
            )
        ))

        fig.add_trace(go.Bar(
            x=scenario.index,
            y=scenario["ProductRevenue"],
            name="Product Revenue",
            marker_color="#b88152",
            customdata=np.stack([scenario["ProductMix"], scenario["Revenue"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Product Revenue: $%{y:.2f}M<br>"
                "Product Mix: %{customdata[0]:.1f}%<br>"
                "Total Revenue: $%{customdata[1]:.2f}M"
                "<extra></extra>"
            )
        ))

        fig.add_trace(go.Scatter(
            x=scenario.index,
            y=scenario["ProfitMargin"],
            name="Profit Margin %",
            mode="lines+markers",
            yaxis="y2",
            line=dict(width=3, color="#ffffff"),
            customdata=np.stack([scenario["Profit"], scenario["Revenue"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Blended Margin: %{y:.2f}%<br>"
                "Estimated Profit: $%{customdata[0]:.2f}M<br>"
                "Total Revenue: $%{customdata[1]:.2f}M"
                "<extra></extra>"
            )
        ))

        if not below_benchmark.empty:
            fig.add_trace(go.Scatter(
                x=below_benchmark.index,
                y=below_benchmark["ProfitMargin"],
                name="Below Benchmark",
                mode="markers",
                marker=dict(size=10, color="#a33a2a"),
                yaxis="y2",
                customdata=np.stack([below_benchmark["Profit"], below_benchmark["Revenue"]], axis=-1),
                hovertemplate=(
                    "Year %{x}<br>"
                    "Margin: %{y:.2f}% (below benchmark)<br>"
                    "Estimated Profit: $%{customdata[0]:.2f}M<br>"
                    "Total Revenue: $%{customdata[1]:.2f}M"
                    "<extra></extra>"
                )
            ))

        fig.add_trace(go.Scatter(
            x=scenario.index,
            y=[benchmark_margin] * len(scenario.index),
            name="Benchmark Margin",
            mode="lines",
            yaxis="y2",
            line=dict(dash="dash", color="#87ceeb"),
            hovertemplate="Benchmark Margin Target: %{y:.2f}%<extra></extra>"
        ))

        fig.update_layout(
            title="Revenue Mix & Profit Margin Projection",
            xaxis_title="Year",
            yaxis=dict(title="Revenue ($M)"),
            yaxis2=dict(
                title="Profit Margin (%)",
                overlaying="y",
                side="right",
                range=[15, 30],
                showgrid=False
            ),
            barmode="stack",
            height=600
        )
        apply_bensonwood_figure_style(fig)
        st.plotly_chart(fig, use_container_width=True)

    elif selected_chart == "Required Product Volume":
        required_fig = go.Figure()
        required_fig.add_trace(go.Bar(
            x=scenario.index,
            y=scenario["ProductRevenue"],
            name="Projected Product Revenue",
            marker_color="#2f5a51",
            customdata=np.stack(
                [scenario["RequiredProductRevenueAtBenchmark"], scenario["RequiredProductMixAtBenchmark"]],
                axis=-1
            ),
            hovertemplate=(
                "Year %{x}<br>"
                "Projected Product Revenue: $%{y:.2f}M<br>"
                "Required at Benchmark: $%{customdata[0]:.2f}M<br>"
                "Required Product Mix: %{customdata[1]:.1f}%"
                "<extra></extra>"
            )
        ))
        required_fig.add_trace(go.Scatter(
            x=scenario.index,
            y=scenario["RequiredProductRevenueAtBenchmark"],
            name="Required Product Revenue to Hit Benchmark",
            mode="lines+markers",
            line=dict(color="#b88152", width=3),
            customdata=np.stack([scenario["ProductRevenue"], scenario["ProfitMargin"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Required Product Revenue: $%{y:.2f}M<br>"
                "Projected Product Revenue: $%{customdata[0]:.2f}M<br>"
                "Projected Blended Margin: %{customdata[1]:.2f}%"
                "<extra></extra>"
            )
        ))
        required_fig.update_layout(
            title="Required Product Volume to Maintain Benchmark Profit",
            xaxis_title="Year",
            yaxis_title="Product Revenue ($M)",
            height=600
        )
        apply_bensonwood_figure_style(required_fig)
        st.plotly_chart(required_fig, use_container_width=True)

    elif selected_chart == "Baseline vs Transition":
        comparison_fig = go.Figure()
        comparison_fig.add_trace(go.Scatter(
            x=scenario.index,
            y=baseline_scenario["CumulativeProfit"],
            name="Baseline Cumulative Profit",
            mode="lines+markers",
            line=dict(width=3, color="#7f9b90"),
            customdata=np.stack([baseline_scenario["Profit"], baseline_scenario["ProfitMargin"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Baseline Cumulative Profit: $%{y:.2f}M<br>"
                "Baseline Annual Profit: $%{customdata[0]:.2f}M<br>"
                "Baseline Margin: %{customdata[1]:.2f}%"
                "<extra></extra>"
            )
        ))
        comparison_fig.add_trace(go.Scatter(
            x=scenario.index,
            y=scenario["CumulativeProfit"],
            name="Transition Cumulative Profit",
            mode="lines+markers",
            line=dict(width=3, color="#2f5a51"),
            customdata=np.stack([scenario["Profit"], scenario["ProfitMargin"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Transition Cumulative Profit: $%{y:.2f}M<br>"
                "Transition Annual Profit: $%{customdata[0]:.2f}M<br>"
                "Transition Margin: %{customdata[1]:.2f}%"
                "<extra></extra>"
            )
        ))
        comparison_fig.update_layout(
            title="Baseline vs Transition Cumulative Profit Comparison",
            xaxis_title="Year",
            yaxis_title="Cumulative Profit ($M)",
            height=600
        )
        apply_bensonwood_figure_style(comparison_fig)
        st.plotly_chart(comparison_fig, use_container_width=True)

    else:
        crossover_fig = go.Figure()
        crossover_fig.add_trace(go.Scatter(
            x=scenario.index,
            y=scenario["CumulativeProfit"] - baseline_scenario["CumulativeProfit"],
            name="Transition Advantage",
            mode="lines+markers",
            line=dict(width=3, color="#2f5a51"),
            customdata=np.stack([scenario["CumulativeProfit"], baseline_scenario["CumulativeProfit"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Cumulative Difference: $%{y:.2f}M<br>"
                "Transition Cumulative: $%{customdata[0]:.2f}M<br>"
                "Baseline Cumulative: $%{customdata[1]:.2f}M"
                "<extra></extra>"
            )
        ))
        crossover_fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="#7f9b90",
            annotation_text="Break-even line"
        )
        if crossover_year is not None:
            crossover_value = (
                scenario.loc[crossover_year, "CumulativeProfit"]
                - baseline_scenario.loc[crossover_year, "CumulativeProfit"]
            )
            crossover_fig.add_trace(go.Scatter(
                x=[crossover_year],
                y=[crossover_value],
                mode="markers+text",
                text=[f"Crossover: Year {crossover_year}"],
                textposition="top center",
                marker=dict(size=12, color="#b88152"),
                name="Crossover Year",
                customdata=np.array([[
                    scenario.loc[crossover_year, "CumulativeProfit"],
                    baseline_scenario.loc[crossover_year, "CumulativeProfit"]
                ]]),
                hovertemplate=(
                    "Year %{x}<br>"
                    "Crossover Difference: $%{y:.2f}M<br>"
                    "Transition Cumulative: $%{customdata[0]:.2f}M<br>"
                    "Baseline Cumulative: $%{customdata[1]:.2f}M"
                    "<extra></extra>"
                )
            ))

        crossover_fig.update_layout(
            title="Cumulative Profit Curve with Crossover Year",
            xaxis_title="Year",
            yaxis_title="Cumulative Profit Difference vs Baseline ($M)",
            height=600
        )
        apply_bensonwood_figure_style(crossover_fig)
        st.plotly_chart(crossover_fig, use_container_width=True)

# --- Executive Insights ---
with col3:
    st.header("Executive Insights")
    st.markdown(f"""
    - Ending Revenue: **${scenario['Revenue'].iloc[-1]:.1f}M**
    - Ending Profit Margin: **{scenario['ProfitMargin'].iloc[-1]:.1f}%**
    - Ending Profit: **${scenario['Profit'].iloc[-1]:.1f}M**
    - Benchmark Margin: **{benchmark_margin}%**
    """)

    # Alerts (kept as plain text; now correctly inside the Executive Insights column)
    if not below_benchmark.empty:
        years_list = ", ".join([f"Year {y}" for y in below_benchmark.index])
        st.markdown(f"**Margin below benchmark in:** {years_list}")
    else:
        st.markdown("Margin remains at or above benchmark across all years.")

    if crossover_year is not None:
        st.markdown(f"Cumulative profit crosses above baseline in Year {crossover_year}.")
    else:
        st.markdown("Transition scenario does not cross above baseline cumulative profit within the selected horizon.")

