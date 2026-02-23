import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title='Bensonwood Revenue & Mix Forecaster', layout='wide')

# ---- Logo ----
st.markdown(
    f"""
    <div style='text-align:center; margin-bottom:20px;'>
      <img src='https://bensonwood.com/wp-content/uploads/2021/10/bensonwood-logo-wht.svg' width='280px'>
    </div>
    """,
    unsafe_allow_html=True
)

st.title('Revenue & Product/Custom Mix Forecaster')

# ---- Sidebar Inputs ----
st.sidebar.header('Forecast Settings')
years = st.sidebar.slider('Forecast Horizon (Years)', 5, 15, 10)
start_mix_custom = st.sidebar.slider('Starting Custom %', 40, 80, 60)
target_mix_custom = st.sidebar.slider('Target Custom %', 40, 80, 50)
custom_growth = st.sidebar.number_input('Annual Volume Growth %', min_value=0.0, max_value=50.0, value=5.0, step=0.5)
product_price = st.sidebar.number_input('Product Unit Price', value=150000)
product_cost = st.sidebar.number_input('Product Unit Cost', value=120000)
custom_price = st.sidebar.number_input('Custom Unit Price', value=250000)
custom_cost = st.sidebar.number_input('Custom Unit Cost', value=180000)

# ---- Custom Mix Curve Input (C) ----
st.sidebar.markdown('**Custom Mix per Year (%)**')
custom_mix_curve = []
for i in range(years):
    val = st.sidebar.slider(f'Year {i+1} Custom %', 40, 80, int(start_mix_custom + (target_mix_custom-start_mix_custom)*(i/(years-1))))
    custom_mix_curve.append(val)

# ---- Baseline Volume Assumptions ----
base_custom_units = st.sidebar.number_input('Starting Custom Units', value=10)
base_product_units = st.sidebar.number_input('Starting Product Units', value=8)

# ---- Prepare DataFrame ----
df = pd.DataFrame({'Year': range(1, years+1)})

# Annual growth factor
growth_factor = 1 + (custom_growth/100)

# Compute baseline volumes (constant 60/40 mix growth)
df['BaselineCustomUnits'] = [base_custom_units * (growth_factor**i) for i in range(years)]
df['BaselineProductUnits'] = [base_product_units * (growth_factor**i) for i in range(years)]
df['BaselineProfit'] = df['BaselineCustomUnits']*(custom_price-custom_cost) + df['BaselineProductUnits']*(product_price-product_cost)

# Scenario: apply custom curve
scenario_custom_units = []
scenario_product_units = []
for i, year_custom_pct in enumerate(custom_mix_curve):
    total_units = df['BaselineCustomUnits'][i] + df['BaselineProductUnits'][i]
    scenario_custom_units.append(total_units * (year_custom_pct/100))
    scenario_product_units.append(total_units * ((100-year_custom_pct)/100))

df['ScenarioCustomUnits'] = scenario_custom_units
df['ScenarioProductUnits'] = scenario_product_units
df['ScenarioProfit'] = df['ScenarioCustomUnits']*(custom_price-custom_cost) + df['ScenarioProductUnits']*(product_price-product_cost)

# Compute shortfall and required product volume to match baseline profit
df['ProfitShortfall'] = np.maximum(0, df['BaselineProfit'] - df['ScenarioProfit'])
df['RequiredProductUnits'] = df['ScenarioProductUnits'] + df['ProfitShortfall']/(product_price-product_cost)
df['VolumeFactor'] = df['RequiredProductUnits']/df['ScenarioProductUnits']

# ---- Plots ----
fig_profit = go.Figure()
fig_profit.add_trace(go.Scatter(x=df['Year'], y=df['BaselineProfit'], mode='lines+markers', name='Baseline Profit', line=dict(color='#D71920', width=3)))
fig_profit.add_trace(go.Scatter(x=df['Year'], y=df['ScenarioProfit'], mode='lines+markers', name='Scenario Profit', line=dict(color='#1A1A1A', width=3)))
fig_profit.update_layout(title='Profit Comparison', xaxis_title='Year', yaxis_title='Profit ($)', plot_bgcolor='#FFFFFF')

fig_units = go.Figure()
fig_units.add_trace(go.Bar(x=df['Year'], y=df['RequiredProductUnits'], name='Required Product Units', marker_color='#D71920'))
fig_units.add_trace(go.Bar(x=df['Year'], y=df['ScenarioProductUnits'], name='Planned Product Units', marker_color='#4A4A4A'))
fig_units.update_layout(title='Product Units: Required vs Planned', xaxis_title='Year', yaxis_title='Units', barmode='group', plot_bgcolor='#FFFFFF')

fig_factor = go.Figure()
fig_factor.add_trace(go.Scatter(x=df['Year'], y=df['VolumeFactor'], mode='lines+markers', name='Required Volume Factor', line=dict(color='#D71920', width=3)))
fig_factor.update_layout(title='Required Product Volume Factor', xaxis_title='Year', yaxis_title='Factor of Planned Volume', plot_bgcolor='#FFFFFF')

# ---- Layout ----
st.subheader('Scenario Visualizations')
col1, col2 = st.columns([2,1])

with col1:
    st.plotly_chart(fig_profit, use_container_width=True)
    st.plotly_chart(fig_units, use_container_width=True)
    st.plotly_chart(fig_factor, use_container_width=True)

with col2:
    st.subheader('Executive Insights')
    insights = []
    for i, row in df.iterrows():
        insights.append(f"Year {row['Year']}: Required product units = {row['RequiredProductUnits']:.1f} ({row['VolumeFactor']:.2f}× planned). Scenario profit = ${row['ScenarioProfit']:,.0f}, baseline profit = ${row['BaselineProfit']:,.0f}.")
    st.text_area('Insights', '\n'.join(insights), height=500)
