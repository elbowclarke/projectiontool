import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Bensonwood Revenue Forecaster", layout="wide")

# --- Theme + Branding ---
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

        :root {
            --bw-deep-forest: #1f3a36;
            --bw-forest: #2f5a51;
            --bw-sage: #7f9b90;
            --bw-wood: #b88152;
            --bw-cream: #f4f0ea;
            --bw-text: #1e2a27;
        }

        html, body, [class*="css"] {
            font-family: 'Montserrat', sans-serif;
            color: var(--bw-text);
        }

        .stApp {
            background: linear-gradient(180deg, #fcfbf8 0%, var(--bw-cream) 100%);
        }

        h1, h2, h3 {
            color: var(--bw-deep-forest) !important;
            letter-spacing: 0.2px;
        }

        section[data-testid="stSidebar"] {
            background: #eef3f0;
            border-right: 1px solid #d7e0dc;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div {
            color: var(--bw-deep-forest) !important;
        }

        [data-baseweb="tab-list"] {
            gap: 0.3rem;
        }

        [data-baseweb="tab"] {
            background-color: #dce6e1;
            border-radius: 0.4rem 0.4rem 0 0;
            color: var(--bw-deep-forest);
            font-weight: 600;
            padding: 0.6rem 0.9rem;
        }

        [aria-selected="true"][data-baseweb="tab"] {
            background-color: var(--bw-forest);
            color: #ffffff;
        }

        .stAlert {
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

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
        (df['CustomRevenue'] * custom_margin + df['ProductRevenue'] * product_margin)
        / df['Revenue']
    )

    df['Profit'] = df['Revenue'] * df['ProfitMargin'] / 100

    return df


def apply_bensonwood_figure_style(fig):
    fig.update_layout(
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#ffffff',
        font=dict(family='Montserrat, sans-serif', color='#1e2a27'),
        colorway=['#2f5a51', '#b88152', '#7f9b90', '#1f3a36'],
        legend=dict(bgcolor='rgba(255,255,255,0.85)', bordercolor='#d7e0dc', borderwidth=1),
    )
    fig.update_xaxes(gridcolor='#e6ece9', zerolinecolor='#d7e0dc')
    fig.update_yaxes(gridcolor='#e6ece9', zerolinecolor='#d7e0dc')


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

scenario['CumulativeProfit'] = scenario['Profit'].cumsum()
baseline_scenario['CumulativeProfit'] = baseline_scenario['Profit'].cumsum()

required_profit = scenario['Revenue'] * benchmark_margin / 100
custom_profit = scenario['CustomRevenue'] * custom_margin / 100
if product_margin > 0:
    scenario['RequiredProductRevenueAtBenchmark'] = np.maximum(
        0,
        (required_profit - custom_profit) / (product_margin / 100),
    )
else:
    scenario['RequiredProductRevenueAtBenchmark'] = np.nan

scenario['RequiredProductMixAtBenchmark'] = (
    scenario['RequiredProductRevenueAtBenchmark'] / scenario['Revenue'] * 100
)
scenario['RequiredProductMixAtBenchmark'] = scenario['RequiredProductMixAtBenchmark'].clip(0, 100)

crossover_candidates = scenario[
    scenario['CumulativeProfit'] >= baseline_scenario['CumulativeProfit']
]
crossover_year = int(crossover_candidates.index[0]) if not crossover_candidates.empty else None

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
    tab1, tab2, tab3, tab4 = st.tabs([
        "Revenue Mix & Margin",
        "Required Product Volume",
        "Baseline vs Transition",
        "Cumulative Profit Crossover",
    ])

    with tab1:
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=scenario.index,
            y=scenario['CustomRevenue'],
            name='Custom Revenue',
            marker_color='#2f5a51',
            hovertemplate='Year %{x}<br>Custom Revenue: $%{y:.1f}M'
        ))

        fig.add_trace(go.Bar(
            x=scenario.index,
            y=scenario['ProductRevenue'],
            name='Product Revenue',
            marker_color='#b88152',
            hovertemplate='Year %{x}<br>Product Revenue: $%{y:.1f}M'
        ))

        fig.add_trace(go.Scatter(
            x=scenario.index,
            y=scenario['ProfitMargin'],
            name='Profit Margin %',
            mode='lines+markers',
            yaxis='y2',
            line=dict(width=3, color='#1f3a36'),
            hovertemplate='Year %{x}<br>Blended Margin: %{y:.1f}%'
        ))

        if not below_benchmark.empty:
            fig.add_trace(go.Scatter(
                x=below_benchmark.index,
                y=below_benchmark['ProfitMargin'],
                name='Below Benchmark',
                mode='markers',
                marker=dict(size=10, color='#a33a2a'),
                yaxis='y2',
                hovertemplate='Year %{x}<br>Below Benchmark: %{y:.1f}%'
            ))

        fig.add_trace(go.Scatter(
            x=scenario.index,
            y=[benchmark_margin] * len(scenario.index),
            name='Benchmark Margin',
            mode='lines',
            yaxis='y2',
            line=dict(dash='dash', color='#7f9b90'),
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
            height=600
        )
        apply_bensonwood_figure_style(fig)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        required_fig = go.Figure()
        required_fig.add_trace(go.Bar(
            x=scenario.index,
            y=scenario['ProductRevenue'],
            name='Projected Product Revenue',
            marker_color='#2f5a51',
            hovertemplate='Year %{x}<br>Projected Product Revenue: $%{y:.1f}M'
        ))
        required_fig.add_trace(go.Scatter(
            x=scenario.index,
            y=scenario['RequiredProductRevenueAtBenchmark'],
            name='Required Product Revenue to Hit Benchmark',
            mode='lines+markers',
            line=dict(color='#b88152', width=3),
            hovertemplate='Year %{x}<br>Required Product Revenue: $%{y:.1f}M'
        ))
        required_fig.update_layout(
            title="Required Product Volume to Maintain Benchmark Profit",
            xaxis_title="Year",
            yaxis_title="Product Revenue ($M)",
            height=600
        )
        apply_bensonwood_figure_style(required_fig)
        st.plotly_chart(required_fig, use_container_width=True)

    with tab3:
        comparison_fig = go.Figure()
        comparison_fig.add_trace(go.Scatter(
            x=scenario.index,
            y=baseline_scenario['CumulativeProfit'],
            name='Baseline Cumulative Profit',
            mode='lines+markers',
            line=dict(width=3, color='#7f9b90'),
            hovertemplate='Year %{x}<br>Baseline Cumulative Profit: $%{y:.1f}M'
        ))
        comparison_fig.add_trace(go.Scatter(
            x=scenario.index,
            y=scenario['CumulativeProfit'],
            name='Transition Cumulative Profit',
            mode='lines+markers',
            line=dict(width=3, color='#2f5a51'),
            hovertemplate='Year %{x}<br>Transition Cumulative Profit: $%{y:.1f}M'
        ))
        comparison_fig.update_layout(
            title='Baseline vs Transition Cumulative Profit Comparison',
            xaxis_title='Year',
            yaxis_title='Cumulative Profit ($M)',
            height=600
        )
        apply_bensonwood_figure_style(comparison_fig)
        st.plotly_chart(comparison_fig, use_container_width=True)

    with tab4:
        crossover_fig = go.Figure()
        crossover_fig.add_trace(go.Scatter(
            x=scenario.index,
            y=scenario['CumulativeProfit'] - baseline_scenario['CumulativeProfit'],
            name='Transition Advantage',
            mode='lines+markers',
            line=dict(width=3, color='#2f5a51'),
            hovertemplate='Year %{x}<br>Cumulative Difference: $%{y:.1f}M'
        ))
        crossover_fig.add_hline(
            y=0,
            line_dash='dash',
            line_color='#7f9b90',
            annotation_text='Break-even line'
        )
        if crossover_year is not None:
            crossover_value = (
                scenario.loc[crossover_year, 'CumulativeProfit']
                - baseline_scenario.loc[crossover_year, 'CumulativeProfit']
            )
            crossover_fig.add_trace(go.Scatter(
                x=[crossover_year],
                y=[crossover_value],
                mode='markers+text',
                text=[f'Crossover: Year {crossover_year}'],
                textposition='top center',
                marker=dict(size=12, color='#b88152'),
                name='Crossover Year',
                hovertemplate='Year %{x}<br>Crossover Difference: $%{y:.1f}M'
            ))

        crossover_fig.update_layout(
            title='Cumulative Profit Curve with Crossover Year',
            xaxis_title='Year',
            yaxis_title='Cumulative Profit Difference vs Baseline ($M)',
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

    if not below_benchmark.empty:
        years_list = ", ".join([f"Year {y}" for y in below_benchmark.index])
        st.error(f"Margin falls below benchmark in: {years_list}")
    else:
        st.success("Margin remains at or above benchmark across all years.")

    st.markdown("### Chart Guide")
    st.markdown(
        """
        **Revenue Mix & Margin**
        - Shows where total revenue comes from each year (custom vs product work).
        - The line shows your blended margin, so leaders can quickly see when the business is getting more or less profitable.
        - Red dots call out years where the margin drops below your benchmark.

        **Required Product Volume to Maintain Benchmark Profit**
        - Compares projected product revenue against the product revenue needed to keep benchmark profit.
        - If the required line sits above projected bars, leadership knows the plan needs either more product sales, better pricing, or lower costs.
        - This makes the profit target concrete by translating it into required product volume.

        **Baseline vs Transition Cumulative Comparison**
        - Compares total profit accumulated over time for two paths: staying at today's mix vs moving toward the target mix.
        - This helps executives evaluate the full journey, not just one year at a time.
        - A widening gap signals one strategy compounding faster than the other.

        **Cumulative Profit Curve with Crossover Year**
        - Tracks the running profit advantage (or disadvantage) of the transition compared to baseline.
        - The zero line is break-even: above it means transition has generated more total profit than baseline.
        - The crossover marker shows when the transition strategy starts to pull ahead on a cumulative basis.
        """
    )

    if crossover_year is not None:
        st.info(f"Cumulative profit crosses above baseline in Year {crossover_year}.")
    else:
        st.warning("Transition scenario does not cross above baseline cumulative profit within the selected horizon.")
