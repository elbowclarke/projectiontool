import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# IMPORTANT: Must be first Streamlit call and only once
st.set_page_config(page_title="Bensonwood Revenue Forecast", layout="wide")

# --- Theme + Branding ---
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

        :root {
            --bw-bg: #1d2f2b;     /* page background (lighter green) */
            --bw-panel: #162321;  /* main panel */
            --bw-panel-2: #1d2f2b;/* sidebar */
            --bw-border: #2d4540;
            --bw-text: #e7efec;
            --bw-muted-text: #b9cbc5;

            --bw-forest: #2f5a51;
            --bw-sage:   #7f9b90;
            --bw-wood:   #b88152;
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
            padding-top: 2.0rem; /* clear the chrome bar */
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
        /* Pull sidebar content up */
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0.25rem !important;
            margin-top: -8px !important;
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
        section[data-testid="stSidebar"] [data-baseweb="typography"] {
            background: transparent !important;
        }

        /* Slider track/fill visible */
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
        /* Slider min/max labels */
        [data-baseweb="slider"] [data-testid="stTickBarMin"],
        [data-baseweb="slider"] [data-testid="stTickBarMax"],
        [data-baseweb="slider"] [data-testid="stTickBarMin"] *,
        [data-baseweb="slider"] [data-testid="stTickBarMax"] * {
            background: transparent !important;
            color: #ffffff !important;
        }

        /* Tooltip */
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
st.markdown("Model the revenue, profit, and overhead implications of holding Custom (Tier 3) steady while growing Tier 1 and Tier 2.")

# --------------------------
# Sidebar: Inputs (Tier model)
# --------------------------
st.sidebar.header("Scenario Inputs")

years = st.sidebar.slider(
    "Planning Horizon (Years)",
    5, 15, 10, 1,
    help="Number of years to model."
)

benchmark_op_margin = st.sidebar.slider(
    "Benchmark Operating Margin %",
    5, 25, 15, 1,
    help="Target operating margin (after overhead). Used for the benchmark line and alerts."
)

st.sidebar.markdown("---")
st.sidebar.subheader("Tier 3 (Custom) — Held Constant")

tier3_revenue = st.sidebar.number_input(
    "Tier 3 Annual Revenue ($M)",
    1.0, 200.0, 21.8, 0.1,
    help="Annual revenue from Custom / Tier 3 work. Held constant across the horizon."
)
tier3_gm = st.sidebar.slider(
    "Tier 3 Gross Margin %",
    10, 40, 25, 1,
    help="Gross margin on Tier 3 revenue (before overhead)."
)
tier3_projects = st.sidebar.number_input(
    "Tier 3 Projects (fixed)",
    1, 200, 20, 1,
    help="Tier 3 project count. Held constant (used for operational load + variable overhead)."
)

st.sidebar.markdown("---")
st.sidebar.subheader("Tier 2 (Product — higher-touch)")

tier2_price = st.sidebar.number_input(
    "Tier 2 Avg Revenue per Project ($M)",
    0.10, 10.00, 0.95, 0.05,
    help="Average recognized revenue per Tier 2 project."
)
tier2_gm = st.sidebar.slider(
    "Tier 2 Gross Margin %",
    5, 35, 20, 1,
    help="Gross margin on Tier 2 revenue (before overhead)."
)
tier2_projects0 = st.sidebar.number_input(
    "Tier 2 Starting Projects (Year 1)",
    0, 500, 15, 1,
    help="Tier 2 project volume in Year 1."
)
tier2_growth = st.sidebar.slider(
    "Tier 2 Project Growth % / Year",
    0, 40, 10, 1,
    help="Annual growth rate in Tier 2 projects."
)

st.sidebar.markdown("---")
st.sidebar.subheader("Tier 1 (Product — most standardized)")

tier1_price = st.sidebar.number_input(
    "Tier 1 Avg Revenue per Project ($M)",
    0.05, 10.00, 0.55, 0.05,
    help="Average recognized revenue per Tier 1 project."
)
tier1_gm = st.sidebar.slider(
    "Tier 1 Gross Margin %",
    1, 30, 14, 1,
    help="Gross margin on Tier 1 revenue (before overhead)."
)
tier1_projects0 = st.sidebar.number_input(
    "Tier 1 Starting Projects (Year 1)",
    0, 500, 25, 1,
    help="Tier 1 project volume in Year 1."
)
tier1_growth = st.sidebar.slider(
    "Tier 1 Project Growth % / Year",
    0, 60, 18, 1,
    help="Annual growth rate in Tier 1 projects."
)

st.sidebar.markdown("---")
st.sidebar.subheader("Overhead Model")

fixed_overhead = st.sidebar.number_input(
    "Fixed Overhead ($M / year)",
    0.0, 50.0, 7.5, 0.1,
    help="Annual fixed overhead (G&A / leadership / facilities / support). Subtracted from gross profit."
)

st.sidebar.markdown("**Variable Overhead (per project)**")
voh_t3 = st.sidebar.number_input(
    "Tier 3 Variable OH ($k / project)",
    0.0, 500.0, 40.0, 5.0,
    help="Overhead/cost burden per Tier 3 project (PM load, supervision, admin burden)."
)
voh_t2 = st.sidebar.number_input(
    "Tier 2 Variable OH ($k / project)",
    0.0, 500.0, 25.0, 5.0,
    help="Overhead/cost burden per Tier 2 project."
)
voh_t1 = st.sidebar.number_input(
    "Tier 1 Variable OH ($k / project)",
    0.0, 500.0, 20.0, 5.0,
    help="Overhead/cost burden per Tier 1 project. Even if smaller, volume can make it dominate."
)

# --------------------------
# Model
# --------------------------
def project_portfolio(
    years_: int,
    t3_rev_m: float,
    t3_gm_pct: float,
    t3_projects_fixed: int,
    t2_price_m: float,
    t2_gm_pct: float,
    t2_projects_start: int,
    t2_growth_pct: float,
    t1_price_m: float,
    t1_gm_pct: float,
    t1_projects_start: int,
    t1_growth_pct: float,
    fixed_oh_m: float,
    voh_t3_k: float,
    voh_t2_k: float,
    voh_t1_k: float,
):
    df = pd.DataFrame(index=range(1, years_ + 1))

    # Projects
    df["T3_Projects"] = int(t3_projects_fixed)
    df["T2_Projects"] = np.round(t2_projects_start * ((1 + t2_growth_pct / 100) ** (df.index - 1))).astype(int)
    df["T1_Projects"] = np.round(t1_projects_start * ((1 + t1_growth_pct / 100) ** (df.index - 1))).astype(int)

    df["TotalProjects"] = df["T1_Projects"] + df["T2_Projects"] + df["T3_Projects"]

    # Revenue
    df["T3_Revenue"] = float(t3_rev_m)
    df["T2_Revenue"] = df["T2_Projects"] * float(t2_price_m)
    df["T1_Revenue"] = df["T1_Projects"] * float(t1_price_m)
    df["TotalRevenue"] = df["T1_Revenue"] + df["T2_Revenue"] + df["T3_Revenue"]

    # Mix (revenue share)
    df["T3_Share"] = (df["T3_Revenue"] / df["TotalRevenue"]) * 100
    df["T2_Share"] = (df["T2_Revenue"] / df["TotalRevenue"]) * 100
    df["T1_Share"] = (df["T1_Revenue"] / df["TotalRevenue"]) * 100

    # Gross profit
    df["T3_GrossProfit"] = df["T3_Revenue"] * (t3_gm_pct / 100)
    df["T2_GrossProfit"] = df["T2_Revenue"] * (t2_gm_pct / 100)
    df["T1_GrossProfit"] = df["T1_Revenue"] * (t1_gm_pct / 100)
    df["GrossProfit"] = df["T1_GrossProfit"] + df["T2_GrossProfit"] + df["T3_GrossProfit"]

    # Overhead
    df["FixedOverhead"] = float(fixed_oh_m)
    df["VarOverhead"] = (
        df["T3_Projects"] * (voh_t3_k / 1000.0)
        + df["T2_Projects"] * (voh_t2_k / 1000.0)
        + df["T1_Projects"] * (voh_t1_k / 1000.0)
    )
    df["TotalOverhead"] = df["FixedOverhead"] + df["VarOverhead"]

    # Operating profit & margin
    df["OperatingProfit"] = df["GrossProfit"] - df["TotalOverhead"]
    df["OperatingMargin"] = np.where(df["TotalRevenue"] > 0, (df["OperatingProfit"] / df["TotalRevenue"]) * 100, np.nan)

    # Efficiency metrics
    df["ProfitPerProject_k"] = np.where(df["TotalProjects"] > 0, (df["OperatingProfit"] / df["TotalProjects"]) * 1000, np.nan)
    df["OverheadPerProject_k"] = np.where(df["TotalProjects"] > 0, (df["TotalOverhead"] / df["TotalProjects"]) * 1000, np.nan)

    return df


scenario = project_portfolio(
    years,
    tier3_revenue,
    tier3_gm,
    tier3_projects,
    tier2_price,
    tier2_gm,
    tier2_projects0,
    tier2_growth,
    tier1_price,
    tier1_gm,
    tier1_projects0,
    tier1_growth,
    fixed_overhead,
    voh_t3,
    voh_t2,
    voh_t1,
)

# Baseline: Tier 3 held constant, Tier 1 and Tier 2 stay flat at Year 1 projects (no growth)
baseline = project_portfolio(
    years,
    tier3_revenue,
    tier3_gm,
    tier3_projects,
    tier2_price,
    tier2_gm,
    tier2_projects0,
    0,  # no growth
    tier1_price,
    tier1_gm,
    tier1_projects0,
    0,  # no growth
    fixed_overhead,
    voh_t3,
    voh_t2,
    voh_t1,
)

scenario["CumulativeOperatingProfit"] = scenario["OperatingProfit"].cumsum()
baseline["CumulativeOperatingProfit"] = baseline["OperatingProfit"].cumsum()

# Below-benchmark years
below_benchmark = scenario[scenario["OperatingMargin"] < benchmark_op_margin]

# Crossover year (transition vs baseline cumulative)
crossover_candidates = scenario[scenario["CumulativeOperatingProfit"] >= baseline["CumulativeOperatingProfit"]]
crossover_year = int(crossover_candidates.index[0]) if not crossover_candidates.empty else None

# Required product revenue to hit benchmark (scale Tier 1+2 volumes together by factor k)
def required_scale_to_hit_benchmark(row, bm_pct):
    bm = bm_pct / 100.0
    A = float(row["T3_Revenue"])
    B = float(row["T3_GrossProfit"] - row["FixedOverhead"] - (row["T3_Projects"] * (voh_t3 / 1000.0)))

    # Base product economics for that year (Tier1+Tier2 together)
    R = float(row["T1_Revenue"] + row["T2_Revenue"])
    GP = float(row["T1_GrossProfit"] + row["T2_GrossProfit"])
    VOH = float((row["T1_Projects"] * (voh_t1 / 1000.0)) + (row["T2_Projects"] * (voh_t2 / 1000.0)))

    denom = (GP - VOH) - bm * R
    numer = bm * A - B

    # If denom <= 0, scaling product does not improve benchmark math in a way that can reach target.
    if abs(denom) < 1e-9:
        return np.nan
    k = numer / denom

    # If k <= 1, current plan already meets (or exceeds) benchmark on required scaling basis.
    # Return required product revenue (scaled) but don't go below current.
    return max(0.0, k)  # allow >1 (needs more), <1 (already enough) becomes 0 for "extra needed"


scenario["RequiredScaleK"] = scenario.apply(lambda r: required_scale_to_hit_benchmark(r, benchmark_op_margin), axis=1)

# Required product revenue at benchmark (using scaling factor on Tier1+Tier2 revenues)
scenario["ProductRevenue"] = scenario["T1_Revenue"] + scenario["T2_Revenue"]
scenario["RequiredProductRevenueAtBenchmark"] = np.where(
    scenario["RequiredScaleK"].isna(),
    np.nan,
    scenario["ProductRevenue"] * scenario["RequiredScaleK"]
)

# Required additional product revenue beyond projected
scenario["AdditionalProductRevenueNeeded"] = scenario["RequiredProductRevenueAtBenchmark"] - scenario["ProductRevenue"]
scenario["AdditionalProductRevenueNeeded"] = scenario["AdditionalProductRevenueNeeded"].clip(lower=0)

# --------------------------
# Plot styling helper
# --------------------------
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

# --------------------------
# Layout
# --------------------------
col1, col2, col3 = st.columns([1, 2, 1])

chart_options = [
    "Revenue Mix & Operating Margin",
    "Required Product Volume",
    "Baseline vs Expansion",
    "Cumulative Profit Crossover",
]
selected_chart = col2.radio("Chart Tabs", chart_options, horizontal=True, label_visibility="collapsed")

chart_guides = {
    "Revenue Mix & Operating Margin": """
### How to read this chart (plain English)

This answers: **“If Custom stays flat and Product grows, what happens to our revenue mix and operating margin?”**

- The **stacked bars** show total revenue each year, split by **Tier 3 (Custom)**, **Tier 2**, and **Tier 1**.
- The **white line** is **operating margin** (profit after overhead).
- The **blue dashed line** is your **benchmark operating margin**.
- **Red dots** indicate “pressure years” when operating margin falls below benchmark.

If you bias growth heavily toward Tier 1, you should see:
- total revenue increasing,
- project load rising,
- and operating margin tightening (if Tier 1 has lower margin / higher overhead burden).
""",
    "Required Product Volume": """
### How to read this chart (plain English)

This answers: **“How much Product revenue do we need to hit our benchmark operating margin?”**

- The **bar** is projected combined **Tier 1 + Tier 2 product revenue**.
- The **line** is the **product revenue required** to reach benchmark operating margin, given:
  - Tier 3 revenue held constant,
  - tier gross margins,
  - fixed overhead,
  - and variable overhead per project.

If the required line sits above the bars, the model is effectively saying:
**“To hit benchmark, we need either more product volume, better product gross margin, or lower overhead.”**
""",
    "Baseline vs Expansion": """
### How to read this chart (plain English)

This answers: **“Are we better off growing Tier 1 & Tier 2, compared with keeping them flat?”**

- **Baseline** holds Tier 1 and Tier 2 project volumes flat at Year 1.
- **Expansion** grows Tier 1 and Tier 2 by your chosen annual growth rates.
- This chart shows **cumulative operating profit** (profit after overhead) over time.

If the lines barely separate, it means growth is adding workload but not much incremental operating profit.
""",
    "Cumulative Profit Crossover": """
### How to read this chart (plain English)

This answers: **“When does the expansion strategy pay back?”**

- The line is: **(Expansion cumulative operating profit) − (Baseline cumulative operating profit)**.
- Above zero means you’re ahead overall.
- The marker shows the first year you pull ahead, if it happens.
""",
}

with col1:
    st.markdown("### Chart Guide")
    st.markdown(chart_guides[selected_chart])

with col2:
    if selected_chart == "Revenue Mix & Operating Margin":
        fig = go.Figure()

        # Stacked revenue bars: Tier 3, Tier 2, Tier 1
        fig.add_trace(go.Bar(
            x=scenario.index,
            y=scenario["T3_Revenue"],
            name="Tier 3 (Custom) Revenue",
            marker_color="#2f5a51",
            customdata=np.stack([scenario["T3_Share"], scenario["TotalRevenue"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Tier 3 Revenue: $%{y:.2f}M<br>"
                "Tier 3 Share: %{customdata[0]:.1f}%<br>"
                "Total Revenue: $%{customdata[1]:.2f}M"
                "<extra></extra>"
            )
        ))
        fig.add_trace(go.Bar(
            x=scenario.index,
            y=scenario["T2_Revenue"],
            name="Tier 2 Revenue",
            marker_color="#7f9b90",
            customdata=np.stack([scenario["T2_Share"], scenario["T2_Projects"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Tier 2 Revenue: $%{y:.2f}M<br>"
                "Tier 2 Share: %{customdata[0]:.1f}%<br>"
                "Tier 2 Projects: %{customdata[1]:.0f}"
                "<extra></extra>"
            )
        ))
        fig.add_trace(go.Bar(
            x=scenario.index,
            y=scenario["T1_Revenue"],
            name="Tier 1 Revenue",
            marker_color="#b88152",
            customdata=np.stack([scenario["T1_Share"], scenario["T1_Projects"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Tier 1 Revenue: $%{y:.2f}M<br>"
                "Tier 1 Share: %{customdata[0]:.1f}%<br>"
                "Tier 1 Projects: %{customdata[1]:.0f}"
                "<extra></extra>"
            )
        ))

        # Operating margin line
        fig.add_trace(go.Scatter(
            x=scenario.index,
            y=scenario["OperatingMargin"],
            name="Operating Margin %",
            mode="lines+markers",
            yaxis="y2",
            line=dict(width=3, color="#ffffff"),
            customdata=np.stack([scenario["OperatingProfit"], scenario["TotalOverhead"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Operating Margin: %{y:.2f}%<br>"
                "Operating Profit: $%{customdata[0]:.2f}M<br>"
                "Total Overhead: $%{customdata[1]:.2f}M"
                "<extra></extra>"
            )
        ))

        # Below-benchmark markers
        if not below_benchmark.empty:
            fig.add_trace(go.Scatter(
                x=below_benchmark.index,
                y=below_benchmark["OperatingMargin"],
                name="Below Benchmark",
                mode="markers",
                marker=dict(size=10, color="#a33a2a"),
                yaxis="y2",
                customdata=np.stack([below_benchmark["OperatingProfit"], below_benchmark["TotalProjects"]], axis=-1),
                hovertemplate=(
                    "Year %{x}<br>"
                    "Operating Margin: %{y:.2f}% (below benchmark)<br>"
                    "Operating Profit: $%{customdata[0]:.2f}M<br>"
                    "Total Projects: %{customdata[1]:.0f}"
                    "<extra></extra>"
                )
            ))

        # Benchmark line
        fig.add_trace(go.Scatter(
            x=scenario.index,
            y=[benchmark_op_margin] * len(scenario.index),
            name="Benchmark Operating Margin",
            mode="lines",
            yaxis="y2",
            line=dict(dash="dash", color="#87ceeb"),
            hovertemplate="Benchmark Target: %{y:.2f}%<extra></extra>"
        ))

        fig.update_layout(
            title="Tier-Based Revenue Mix & Operating Margin",
            xaxis_title="Year",
            yaxis=dict(title="Revenue ($M)"),
            yaxis2=dict(
                title="Operating Margin (%)",
                overlaying="y",
                side="right",
                range=[0, 25],
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
            name="Projected Tier 1 + Tier 2 Revenue",
            marker_color="#2f5a51",
            customdata=np.stack(
                [scenario["RequiredProductRevenueAtBenchmark"], scenario["AdditionalProductRevenueNeeded"]],
                axis=-1
            ),
            hovertemplate=(
                "Year %{x}<br>"
                "Projected Product Revenue: $%{y:.2f}M<br>"
                "Required at Benchmark: $%{customdata[0]:.2f}M<br>"
                "Additional Needed: $%{customdata[1]:.2f}M"
                "<extra></extra>"
            )
        ))

        required_fig.add_trace(go.Scatter(
            x=scenario.index,
            y=scenario["RequiredProductRevenueAtBenchmark"],
            name="Required Product Revenue to Hit Benchmark",
            mode="lines+markers",
            line=dict(color="#b88152", width=3),
            customdata=np.stack([scenario["OperatingMargin"], scenario["TotalProjects"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Required Product Revenue: $%{y:.2f}M<br>"
                "Projected Operating Margin: %{customdata[0]:.2f}%<br>"
                "Total Projects: %{customdata[1]:.0f}"
                "<extra></extra>"
            )
        ))

        required_fig.update_layout(
            title="Required Tier 1 + Tier 2 Revenue to Maintain Benchmark Operating Margin",
            xaxis_title="Year",
            yaxis_title="Product Revenue ($M)",
            height=600
        )
        apply_bensonwood_figure_style(required_fig)
        st.plotly_chart(required_fig, use_container_width=True)

    elif selected_chart == "Baseline vs Expansion":
        comparison_fig = go.Figure()

        comparison_fig.add_trace(go.Scatter(
            x=scenario.index,
            y=baseline["CumulativeOperatingProfit"],
            name="Baseline Cumulative Operating Profit",
            mode="lines+markers",
            line=dict(width=3, color="#7f9b90"),
            customdata=np.stack([baseline["OperatingProfit"], baseline["OperatingMargin"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Baseline Cumulative Op Profit: $%{y:.2f}M<br>"
                "Baseline Annual Op Profit: $%{customdata[0]:.2f}M<br>"
                "Baseline Op Margin: %{customdata[1]:.2f}%"
                "<extra></extra>"
            )
        ))

        comparison_fig.add_trace(go.Scatter(
            x=scenario.index,
            y=scenario["CumulativeOperatingProfit"],
            name="Expansion Cumulative Operating Profit",
            mode="lines+markers",
            line=dict(width=3, color="#2f5a51"),
            customdata=np.stack([scenario["OperatingProfit"], scenario["OperatingMargin"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Expansion Cumulative Op Profit: $%{y:.2f}M<br>"
                "Expansion Annual Op Profit: $%{customdata[0]:.2f}M<br>"
                "Expansion Op Margin: %{customdata[1]:.2f}%"
                "<extra></extra>"
            )
        ))

        comparison_fig.update_layout(
            title="Baseline vs Expansion: Cumulative Operating Profit (After Overhead)",
            xaxis_title="Year",
            yaxis_title="Cumulative Operating Profit ($M)",
            height=600
        )
        apply_bensonwood_figure_style(comparison_fig)
        st.plotly_chart(comparison_fig, use_container_width=True)

    else:
        crossover_fig = go.Figure()

        diff = scenario["CumulativeOperatingProfit"] - baseline["CumulativeOperatingProfit"]

        crossover_fig.add_trace(go.Scatter(
            x=scenario.index,
            y=diff,
            name="Expansion Advantage",
            mode="lines+markers",
            line=dict(width=3, color="#2f5a51"),
            customdata=np.stack([scenario["CumulativeOperatingProfit"], baseline["CumulativeOperatingProfit"]], axis=-1),
            hovertemplate=(
                "Year %{x}<br>"
                "Cumulative Difference: $%{y:.2f}M<br>"
                "Expansion Cumulative: $%{customdata[0]:.2f}M<br>"
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
            crossover_value = float(diff.loc[crossover_year])
            crossover_fig.add_trace(go.Scatter(
                x=[crossover_year],
                y=[crossover_value],
                mode="markers+text",
                text=[f"Crossover: Year {crossover_year}"],
                textposition="top center",
                marker=dict(size=12, color="#b88152"),
                name="Crossover Year",
                hovertemplate=(
                    "Year %{x}<br>"
                    "Crossover Difference: $%{y:.2f}M"
                    "<extra></extra>"
                )
            ))

        crossover_fig.update_layout(
            title="Cumulative Operating Profit Advantage (Expansion vs Baseline)",
            xaxis_title="Year",
            yaxis_title="Cumulative Profit Difference ($M)",
            height=600
        )
        apply_bensonwood_figure_style(crossover_fig)
        st.plotly_chart(crossover_fig, use_container_width=True)

# --------------------------
# Scenario Insights (scrollable, stable)
# --------------------------
with col3:
    st.header("Scenario Insights")

    years_below = ", ".join([f"Year {y}" for y in below_benchmark.index]) if not below_benchmark.empty else "None"
    crossover_text = f"Year {crossover_year}" if crossover_year is not None else "Not within horizon"

    end = scenario.iloc[-1]
    start = scenario.iloc[0]

    # Key derived story items
    t3_start = float(start["T3_Share"])
    t3_end = float(end["T3_Share"])

    proj_start = int(start["TotalProjects"])
    proj_end = int(end["TotalProjects"])

    opm_start = float(start["OperatingMargin"])
    opm_end = float(end["OperatingMargin"])

    opp_start = float(start["OperatingProfit"])
    opp_end = float(end["OperatingProfit"])

    ppp_start = float(start["ProfitPerProject_k"])
    ppp_end = float(end["ProfitPerProject_k"])

    # Bias indicator (Tier1 share at end)
    t1_end = float(end["T1_Share"])
    bias_flag = "Tier 1 dominates the mix by the end." if t1_end >= 35 else "Tier 1 does not dominate the mix by the end."

    # Takeaway heuristic
    if below_benchmark.empty and ppp_end >= ppp_start:
        takeaway = "Overall: growth adds volume without degrading profit efficiency (under these assumptions)."
    elif not below_benchmark.empty and ppp_end < ppp_start:
        takeaway = "Overall: growth adds workload and tightens profitability/efficiency (pressure years appear)."
    elif not below_benchmark.empty:
        takeaway = "Overall: benchmark risk appears—tune margins, overhead, or tier mix."
    else:
        takeaway = "Overall: mixed—profit may rise, but profit per project softens."

    insights_html = f"""
    <html>
    <head>
      <style>
        body {{
          margin: 0;
          font-family: Montserrat, sans-serif;
          color: #e7efec;
          background: transparent;
        }}
        .wrap {{
          max-height: 585px;
          overflow-y: auto;
          padding-right: 10px;
        }}
        .rule {{
          border: 0;
          border-top: 1px solid #2d4540;
          margin: 12px 0;
        }}
        h3 {{
          margin: 12px 0 6px 0;
          font-size: 14px;
          font-weight: 700;
        }}
        p, li {{
          font-size: 13px;
          line-height: 1.35;
          margin: 6px 0;
        }}
        ul {{
          margin: 6px 0 6px 18px;
          padding: 0;
        }}
        .takeaway {{
          font-weight: 700;
          margin-top: 0;
        }}
        .muted {{
          color: #b9cbc5;
        }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <p class="takeaway">{takeaway}</p>
        <p class="muted">{bias_flag}</p>
        <hr class="rule"/>

        <h3>What the model is doing</h3>
        <ul>
          <li><strong>Tier 3 (Custom)</strong> revenue is held constant at ${tier3_revenue:.1f}M and projects are fixed at {tier3_projects}.</li>
          <li><strong>Tier 1 and Tier 2</strong> grow via project counts; revenue is price × projects.</li>
          <li><strong>Overhead</strong> is modeled as fixed overhead plus a per-project overhead load by tier.</li>
        </ul>

        <hr class="rule"/>
        <h3>Did we move Custom from ~60% toward 50%?</h3>
        <p>
          <strong>Tier 3 share:</strong> {t3_start:.1f}% → <strong>{t3_end:.1f}%</strong><br/>
          If this doesn't approach your target, it means Tier 1 + Tier 2 are not adding enough revenue, or Tier 3 is too large.
        </p>

        <hr class="rule"/>
        <h3>Operational load (workload)</h3>
        <p>
          <strong>Total projects:</strong> {proj_start} → <strong>{proj_end}</strong><br/>
          When Tier 1 drives most of that increase, the organization feels it as scheduling, coordination, service load, and overhead drag.
        </p>

        <p>
          <strong>Overhead per project:</strong> {float(start["OverheadPerProject_k"]):.1f}k → <strong>{float(end["OverheadPerProject_k"]):.1f}k</strong>
        </p>

        <hr class="rule"/>
        <h3>Profit quality (are we tightening profits?)</h3>
        <p>
          <strong>Operating margin:</strong> {opm_start:.1f}% → <strong>{opm_end:.1f}%</strong><br/>
          <strong>Operating profit:</strong> ${opp_start:.2f}M → <strong>${opp_end:.2f}M</strong>
        </p>

        <p>
          <strong>Profit per project:</strong> {ppp_start:.1f}k → <strong>{ppp_end:.1f}k</strong><br/>
          This is often the clearest indicator of “more work for thinner returns.”
        </p>

        <hr class="rule"/>
        <h3>Benchmark risk</h3>
        <p><strong>Benchmark operating margin:</strong> {benchmark_op_margin}%</p>
        <p><strong>Years below benchmark:</strong> {years_below}</p>
        <p class="muted">If below-benchmark years appear, the levers are: improve Tier 1/2 gross margin, reduce overhead burden, shift more growth to Tier 2, or slow Tier 1 expansion.</p>

        <hr class="rule"/>
        <h3>Payback vs keeping Tier 1 & 2 flat</h3>
        <p><strong>Crossover year:</strong> {crossover_text}</p>
        <p class="muted">Crossover means cumulative operating profit from growth becomes greater than the baseline over time.</p>
      </div>
    </body>
    </html>
    """

    components.html(insights_html, height=585, scrolling=True)
