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

        /* Scenario Insights scroll area */
        .scenario-insights-scroll {
            max-height: 585px;          /* tune if needed */
            overflow-y: auto;
            padding-right: 10px;
        }
        .scenario-insights-scroll h3 {
            margin-top: 0.7rem;
            margin-bottom: 0.3rem;
        }
        .scenario-insights-scroll p, .scenario-insights-scroll li {
            color: var(--bw-text) !important;
            line-height: 1.35;
        }
        .scenario-insights-scroll hr {
            border: 0;
            border-top: 1px solid var(--bw-border);
            margin: 0.8rem 0;
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

# Derived diagnostics (no extra charts)
avg_margin = float(scenario["ProfitMargin"].mean())
min_margin = float(scenario["ProfitMargin"].min())
max_margin = float(scenario["ProfitMargin"].max())
worst_year = int(scenario["ProfitMargin"].idxmin())

ending_revenue = float(scenario["Revenue"].iloc[-1])
ending_profit = float(scenario["Profit"].iloc[-1])
ending_margin = float(scenario["ProfitMargin"].iloc[-1])

baseline_ending_profit = float(baseline_scenario["Profit"].iloc[-1])
ending_profit_delta = ending_profit - baseline_ending_profit

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

# More layperson-friendly chart guides
chart_guides = {
    "Revenue Mix & Margin": """
### What you’re looking at

This view answers: **“What are we selling each year, and how profitable is it overall?”**

- The **stacked bars** show total revenue each year, split into **Custom** (green) and **Product** (wood).
- The **white line** is the company’s **blended profit margin** (how much profit you keep per dollar of revenue).
- The **blue dashed line** is your **benchmark target margin**.
- **Red dots** flag any year where the blended margin drops below your benchmark (a potential “stress year”).
""",
    "Required Product Volume": """
### What you’re looking at

This view answers: **“How much product revenue do we need to keep margins on target?”**

- The **bars** show the **product revenue you’re projecting**.
- The **line** shows the **product revenue required** to maintain the benchmark margin, given:
  - your current custom revenue,
  - custom margin,
  - product margin.

If the **required line is above the bars**, the scenario is saying:
**“We’d need more product volume (or better product margin / costs) to hit the benchmark.”**
""",
    "Baseline vs Transition": """
### What you’re looking at

This view answers: **“Over time, does the transition strategy create more total profit than staying the same?”**

- One line is **Baseline** (no change in mix).
- The other is **Transition** (moving toward the target mix).
- Because this is **cumulative profit**, it’s about the **total dollars earned over time**, not a single year.

If the transition line stays above baseline, the strategy is compounding value faster.
""",
    "Cumulative Profit Crossover": """
### What you’re looking at

This view answers: **“When does the transition pay back?”**

- The line is **Transition cumulative profit minus Baseline cumulative profit**.
- **Above zero** means the transition has generated **more total profit** than the baseline up to that point.
- The **crossover marker** (if it appears) is the first year the transition pulls ahead overall.
""",
}

# --- Left Column (Chart Guide only) ---
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

# --- Scenario Insights (scrollable) ---
with col3:
    st.header("Scenario Insights")

    # Build an HTML block so the scroll container actually wraps all content
    years_list = ", ".join([f"Year {y}" for y in below_benchmark.index]) if not below_benchmark.empty else "None"
    crossover_text = f"Year {crossover_year}" if crossover_year is not None else "Not within horizon"

    # Simple takeaway label (compact)
    if below_benchmark.empty and (crossover_year is None or crossover_year <= max(3, years // 2)):
        takeaway = "Overall: disciplined transition under these assumptions."
    elif not below_benchmark.empty and crossover_year is not None:
        takeaway = "Overall: transition pays back, but includes pressure years."
    elif not below_benchmark.empty and crossover_year is None:
        takeaway = "Overall: high risk—pressure years without payback in horizon."
    else:
        takeaway = "Overall: mixed outcome—consider adjusting margins, growth, or timeline."

    insights_html = f"""
    <div class="scenario-insights-scroll">
        <p><strong>{takeaway}</strong></p>
        <hr/>

        <h3>Assumptions (what you told the model)</h3>
        <ul>
            <li><strong>Planning horizon:</strong> {years} years (how long the shift takes)</li>
            <li><strong>Revenue growth:</strong> {annual_growth_rate}% per year (before mix effects)</li>
            <li><strong>Revenue starts at:</strong> ${baseline_revenue:.1f}M and grows to <strong>${ending_revenue:.1f}M</strong></li>
            <li><strong>Custom mix shifts:</strong> {base_custom_mix}% → <strong>{target_custom_mix}%</strong></li>
            <li><strong>Margins assumed:</strong> Custom {custom_margin}% / Product {product_margin}%</li>
            <li><strong>Benchmark margin:</strong> {benchmark_margin}% (your “do not dip below” target)</li>
        </ul>

        <hr/>
        <h3>Results (what the model projects)</h3>
        <ul>
            <li><strong>Ending blended margin:</strong> {ending_margin:.1f}%</li>
            <li><strong>Ending annual profit:</strong> ${ending_profit:.1f}M</li>
            <li><strong>Profit vs baseline in final year:</strong> {ending_profit_delta:+.1f}M (transition minus baseline)</li>
        </ul>

        <p><strong>Margin stability:</strong><br/>
           Lowest {min_margin:.1f}% • Average {avg_margin:.1f}% • Highest {max_margin:.1f}%<br/>
           Worst year for margin: <strong>Year {worst_year}</strong>
        </p>

        <hr/>
        <h3>Risk watch (where things get tight)</h3>
        <p>
            <strong>Years below benchmark:</strong> {years_list}<br/>
            If this list is not “None”, those are the years you’d likely feel operational pressure
            (pricing, cost, capacity, overhead absorption, or a need for more product volume).
        </p>

        <hr/>
        <h3>Payback (does the strategy win over time?)</h3>
        <p>
            <strong>Crossover year:</strong> {crossover_text}<br/>
            “Crossover” means total profit earned <em>to date</em> under the transition plan becomes greater than
            total profit earned under staying at today’s mix.
        </p>

        <hr/>
        <h3>How to use this in a discussion</h3>
        <ul>
            <li>If margin dips below benchmark, ask: <em>Is the mix change too fast, or are product margins too low?</em></li>
            <li>If required product volume is high, ask: <em>Is the go-to-market plan realistic for that volume?</em></li>
            <li>If payback is late or missing, ask: <em>Do we need a longer horizon, higher growth, or better margins?</em></li>
        </ul>
    </div>
    """

    st.markdown(insights_html, unsafe_allow_html=True)
