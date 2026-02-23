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
st.markdown("Visualize 10-year growth and volume required when shifting from custom-heavy work to more product-focused work.")

# --- Sidebar sliders ---
st.sidebar.header("Scenario Inputs")

years = 10
base_custom_mix = st.sidebar.slider("Baseline Custom Work %", 50, 80, 60, 1)
target_custom_mix = st.sidebar.slider("Target Custom Work %", 40, 70, 50, 1)
baseline_revenue = st.sidebar.number_input("Current Annual Revenue ($M)", 1.0, 100.0, 10.0, 0.1)
baseline_profit_margin = st.sidebar.slider("Baseline Profit Margin %", 5, 40, 20, 1)
product_margin = st.sidebar.slider("Product Work Margin %", 5, 30, 15, 1)
annual_growth_rate = st.sidebar.slider("Annual Revenue Growth Rate %", 0, 25, 8, 1)

# --- Compute projections ---
def project_revenue_mix(years, revenue, growth, base_mix, target_mix, base_margin, product_margin):
    df = pd.DataFrame(index=range(1, years+1))
    df['Revenue'] = revenue * ((1 + growth/100) ** (df.index - 1))
    
    # Linear shift in mix from base_mix -> target_mix
    df['CustomMix'] = np.linspace(base_mix, target_mix, years)
    df['ProductMix'] = 100 - df['CustomMix']
    
    # Compute blended margin
    df['ProfitMargin'] = (df['CustomMix']/100 * base_margin) + (df['ProductMix']/100 * product_margin)
    df['Profit'] = df['Revenue'] * df['ProfitMargin']/100
    
    # Compute product volume required to maintain baseline profit
    baseline_profit = revenue * base_margin / 100
    df['RequiredRevenue_Product'] = baseline_profit / (product_margin/100)
    df['RequiredVolumeFactor'] = df['RequiredRevenue_Product'] / df['Revenue']
    
    return df

baseline = project_revenue_mix(years, baseline_revenue, annual_growth_rate,
                               base_custom_mix, base_custom_mix,
                               baseline_profit_margin, product_margin)

scenario = project_revenue_mix(years, baseline_revenue, annual_growth_rate,
                               base_custom_mix, target_custom_mix,
                               baseline_profit_margin, product_margin)

# --- Tabs for saved scenarios ---
if 'saved_scenarios' not in st.session_state:
    st.session_state.saved_scenarios = {}

col1, col2, col3 = st.columns([1,2,1])

# --- Sliders are in col1 ---
with col1:
    if st.button("Save Current Scenario"):
        scenario_name = st.text_input("Scenario Name", value=f"Scenario {len(st.session_state.saved_scenarios)+1}")
        if scenario_name:
            st.session_state.saved_scenarios[scenario_name] = scenario
            st.success(f"Saved scenario: {scenario_name}")

# --- Charts in col2 ---
with col2:
    fig = go.Figure()

    # Revenue & Profit (primary y-axis)
    fig.add_trace(go.Scatter(x=baseline.index, y=baseline['Revenue'], 
                             mode='lines+markers', name='Baseline Revenue',
                             hovertemplate='Year %{x}<br>Revenue: $%{y:.1f}M'))
    fig.add_trace(go.Scatter(x=scenario.index, y=scenario['Revenue'], 
                             mode='lines+markers', name='Scenario Revenue',
                             hovertemplate='Year %{x}<br>Revenue: $%{y:.1f}M'))
    fig.add_trace(go.Scatter(x=baseline.index, y=baseline['Profit'], 
                             mode='lines+markers', name='Baseline Profit',
                             line=dict(dash='dot'), hovertemplate='Year %{x}<br>Profit: $%{y:.1f}M'))
    fig.add_trace(go.Scatter(x=scenario.index, y=scenario['Profit'], 
                             mode='lines+markers', name='Scenario Profit',
                             line=dict(dash='dot'), hovertemplate='Year %{x}<br>Profit: $%{y:.1f}M'))

    # Required product revenue (secondary y-axis)
    fig.add_trace(go.Scatter(x=scenario.index, y=scenario['RequiredRevenue_Product'], 
                             mode='lines', name='Required Product Revenue',
                             line=dict(color='firebrick', dash='dash'),
                             yaxis="y2",
                             hovertemplate='Year %{x}<br>Required Product Revenue: $%{y:.1f}M'))

    fig.update_layout(
        title="Revenue, Profit, and Required Product Volume Over 10 Years",
        xaxis_title="Year",
        yaxis_title="Revenue / Profit ($M)",
        yaxis2=dict(title="Required Product Revenue ($M)", overlaying='y', side='right'),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        template="plotly_white",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

# --- Executive Insights in col3 ---
with col3:
    st.header("Executive Insights")
    st.markdown("""
    **Scenario Analysis:**  
    - Shifting from a {:.0f}/{:.0f} custom/product mix to {:.0f}/{:.0f} mix over 10 years.
    - Product work has lower margins ({:.0f}%) than custom work ({:.0f}%).
    - Profit growth requires increasing product volume by up to {:.1f}x in Year 10 to maintain baseline profit.
    """.format(base_custom_mix, 100-base_custom_mix,
               target_custom_mix, 100-target_custom_mix,
               product_margin, baseline_profit_margin,
               scenario['RequiredVolumeFactor'].iloc[-1]))
    
    if st.session_state.saved_scenarios:
        st.subheader("Saved Scenarios")
        for name, df_s in st.session_state.saved_scenarios.items():
            st.markdown(f"**{name}**")
            st.dataframe(df_s[['Revenue','Profit','RequiredRevenue_Product']])
