import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# IMPORTANT: Must be first Streamlit call and only once
st.set_page_config(page_title="Bensonwood Revenue Forecast", layout="wide")

# --- Theme + Branding (lighter page bg, sidebar pulled up, rounded main top corners, slider fixes) ---
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

        :root {
            --bw-bg: #1d2f2b;     /* lighter green background */
            --bw-panel: #162321;  /* main panel */
            --bw-panel-2: #1d2f2b;/* sidebar */
            --bw-border: #2d4540;
            --bw-text: #e7efec;
            --bw-muted-text: #b9cbc5;
            --bw-forest: #2f5a51;
            --bw-sage: #7f9b90;
            --bw-wood: #b88152;
        }

        html, body, .stApp {
            font-family: 'Montserrat', sans-serif;
            color: var(--bw-text) !important;
            background: var(--bw-bg) !important;
        }

        /* Streamlit chrome header (top bar) */
        header[data-testid="stHeader"] {
            background-color: var(--bw-bg) !important;
        }
        header[data-testid="stHeader"] > div {
            box-shadow: none !important;
        }

        /* Main content panel */
        .block-container {
            background: var(--bw-panel);
            border: 1px solid var(--bw-border);
            border-radius: 12px;
            border-top-left-radius: 16px !important;
            border-top-right-radius: 16px !important;
            overflow: hidden;
            padding: 1.25rem 1.5rem 1.75rem;
            padding-top: 2.0rem; /* keep content clear of chrome bar */
        }

        h1, h2, h3, h4, p, li, label, span, div {
            color: var(--bw-text) !important;
        }
        h1, h2, h3 { letter-spacing: 0.2px; }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: var(--bw-panel-2);
            border-right: 1px solid var(--bw-border);
        }

        /* Pull sidebar content up so Scenario Inputs aligns under chrome bar */
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0.25rem !important;
            margin-top: -8px !important;
        }
        section[data-testid="stSidebar"] h1:first-child,
        section[data-testid="stSidebar"] h2:first-child,
        section[data-testid="stSidebar"] h3:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

        /* Tabs */
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

        /* Sidebar inputs: remove filled backgrounds */
        section[data-testid="stSidebar"] input[type="number"],
        section[data-testid="stSidebar"] input[type="text"],
        section[data-testid="stSidebar"] textarea {
            background: transparent !important;
            color: #ffffff !important;
            border: 1px solid var(--bw-border) !important;
            box-shadow: none !important;
        }

        /* Avoid label "pills" */
        section[data-testid="stSidebar"] [data-baseweb="typography"] {
            background: transparent !important;
        }

        /* Slider: keep track and fill visible */
        [data-baseweb="slider"] [data-baseweb="progress-bar"],
        [data-baseweb="slider"] [role="progressbar"] {
            background-color: rgba(231, 239, 236, 0.25) !important; /* track */
        }
        [data-baseweb="slider"] [data-baseweb="progress-bar"] > div,
        [data-baseweb="slider"] [role="progressbar"] > div {
            background-color: rgba(231, 239, 236, 0.65) !important; /* fill */
        }

        /* Slider thumb */
        [data-baseweb="slider"] [role="slider"] {
            background-color: #ffffff !important;
            border-color: #ffffff !important;
        }

        /* Slider min/max and tick labels: white text, no background boxes */
        [data-baseweb="slider"] [data-testid="stTickBarMin"],
        [data-baseweb="slider"] [data-testid="stTickBarMax"],
        [data-baseweb="slider"] [data-testid="stTickBarMin"] *,
        [data-baseweb="slider"] [data-testid="stTickBarMax"] * {
            background: transparent !important;
            color: #ffffff !important;
        }

        /* Tooltip bubble: readable */
        [data-baseweb="tooltip"],
        [role="tooltip"] {
            background-color: rgba(0,0,0,0.65) !important;
            color: #ffffff !important;
            border: 1px solid rgba(45, 69, 64, 0.8) !important;
            box-shadow: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header: logo above title, left-biased ---
LOGO_URL = "https://bensonwood.com/wp-content/uploads/2021/10/bensonwood-logo-wht.svg"
st.markdown(
    f"<img src='{LOGO_URL}' width='260' style='display:block; margin: 0 0 8px 0;'>",
    unsafe_allow_html=True
)

st.title("Revenue & Product Mix Forecast")
st.markdown("Model the revenue and profit implications of shifting from custom work toward product-based work.")

# --- Sidebar (organized inputs) ---
st.sidebar.header("Scenario Inputs")

baseline_revenue = st.sidebar.number_input(
    "Current Annual Revenue ($M)",
    1.0, 100.0, 32.5, 0.1,
    help="Total company revenue in millions for the current year."
)

benchmark_margin = st.sidebar.slider(
    "Benchmark Profit Margin %",
    15, 30, 21, 1,
    help="Target or minimum acceptable blended company profit margin."
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

st.sidebar.markdown("---")
st.sidebar.subheader("Transition Projection")

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

    df["Profit"] = df["Revenue"] * df["ProfitMargin"] / 100
    return df


def apply_bensonwood_figure_style(fig):
    # previous color scheme + styling
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

# Additional “useful without breaking layout” metrics (derived, no extra charts)
scenario["RevenueDelta"] = scenario["Revenue"] - baseline_scenario["Revenue"]
scenario["ProfitDelta"] = scenario["Profit"] - baseline_scenario["Profit"]
scenario["CumulativeProfitDelta"] = scenario["CumulativeProfit"] - baseline_scenario["CumulativeProfit"]

avg_margin = float(scenario["ProfitMargin"].mean())
min_margin = float(scenario["ProfitMargin"].min())
max_margin = float(scenario["ProfitMargin"].max())
worst_year = int(scenario["ProfitMargin"].idxmin())

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
- See how total revenue splits between custom and product work each year.
- Track blended margin and the benchmark target line.
- Red points indicate years below benchmark.
""",
    "Required Product Volume": """
**Required Product Volume to Maintain Benchmark Profit**
- Compare projected product revenue to the product revenue required to hold the benchmark margin.
- If required runs above projected, volume/pricing/cost needs to improve.
""",
    "Baseline vs Transition": """
**Baseline vs Transition Cumulative Comparison**
- Compare cumulative profit under two paths: no mix change vs transition to target mix.
- Focuses on durability and compounding over time.
""",
    "Cumulative Profit Crossover": """
**Cumulative Profit Curve with Crossover Year**
- Shows cumulative profit difference (Transition minus Baseline).
- Above zero means the transition has paid back vs baseline to date.
- Marker indicates crossover year (if any).
""",
}

# --- Left Column (Chart Guide only; Scenario Summary removed) ---
with col1:
    st.markdown("### Chart Guide")
    st.markdown(chart_guides[selected_chart])

# --- Center Chart (tabs + alternate diagrams) ---
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

# --- Scenario Insights (Scenario Summary consolidated here) ---
with col3:
    st.header("Scenario Insights")

    st.markdown(f"""
- **Planning Horizon:** {years} years  
- **Revenue Path:** ${baseline_revenue:.1f}M → **${scenario['Revenue'].iloc[-1]:.1f}M**  
- **Custom Mix Shift:** {base_custom_mix}% → **{target_custom_mix}%**  
- **Benchmark Margin:** **{benchmark_margin}%**  
- **Ending Profit Margin:** **{scenario['ProfitMargin'].iloc[-1]:.1f}%**  
- **Ending Profit:** **${scenario['Profit'].iloc[-1]:.1f}M**  
""")

    # Additional helpful (compact) diagnostics
    st.markdown("**Margin Range (min / avg / max):** "
                f"{min_margin:.1f}% / {avg_margin:.1f}% / {max_margin:.1f}%")
    st.markdown(f"**Worst Margin Year:** Year {worst_year}")

    if crossover_year is not None:
        st.markdown(f"**Crossover Year (cumulative vs baseline):** Year {crossover_year}")
    else:
        st.markdown("**Crossover Year (cumulative vs baseline):** Not within horizon")

    # Alerts (plain text, in-frame)
    if not below_benchmark.empty:
        years_list = ", ".join([f"Year {y}" for y in below_benchmark.index])
        st.markdown(f"**Margin below benchmark in:** {years_list}")
    else:
        st.markdown("**Margin below benchmark in:** None")
