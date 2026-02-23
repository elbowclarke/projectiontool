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
def project_mix(years, revenue, growth, base_mix, target_mix, base_margin, product_margin):
    df = pd.DataFrame(index=range(1, years+1))
    df['Revenue'] = revenue * ((1 + growth/100) ** (df.index - 1))
    
    # Linear shift in mix
    df['CustomMix'] = np.linspace(base_mix, target_mix, years)
    df['ProductMix'] = 100 - df['CustomMix']
    
    # Revenue split
    df['CustomRevenue'] = df['Revenue'] * df['CustomMix']/100
    df['ProductRevenue'] = df['Revenue'] * df['ProductMix']/100
    
    # Profit margin
    df['ProfitMargin'] = (df['CustomRevenue']*base_margin + df['ProductRevenue']*product_margin)/df['Revenue']
    df['Profit'] = df['Revenue'] * df['ProfitMargin']/100
    
    return df

scenario = project_mix(years, baseline_revenue, annual_growth_rate,
                       base_custom_mix, target_custom_mix,
                       baseline_profit_margin, product_margin)

# --- Columns layout ---
col1, col2, col3 = st.columns([1,2,1])

# --- Sliders in col1 ---
with col1:
    st.markdown("### Scenario Controls")
    st.write(f"Shifting from **{base_custom_mix}/{100-base_custom_mix}** mix to **{target_custom_mix}/{100-target_custom_mix}** over {years} years.")

# --- Chart in col2 ---
with col2:
    fig = go.Figure()
    
    # Stacked bars for revenue mix
    fig.add_trace(go.Bar(x=scenario.index, y=scenario['CustomRevenue'],
                         name='Custom Work Revenue', marker_color='royalblue',
                         hovertemplate='Year %{x}<br>Custom Revenue: $%{y:.1f}M'))
    fig.add_trace(go.Bar(x=scenario.index, y=scenario['ProductRevenue'],
                         name='Product Work Revenue', marker_color='orange',
                         hovertemplate='Year %{x}<br>Product Revenue: $%{y:.1f}M'))
    
    # Overlay line for profit margin
    fig.add_trace(go.Scatter(x=scenario.index, y=scenario['ProfitMargin'],
                             name='Profit Margin %', mode='lines+markers',
                             line=dict(color='green', width=3), yaxis='y2',
                             hovertemplate='Year %{x}<br>Profit Margin: %{y:.1f}%'))
    
    fig.update_layout(
        title="Revenue Mix & Profit Margin Over 10 Years",
        xaxis_title="Year",
        yaxis=dict(title="Revenue ($M)", side='left'),
        yaxis2=dict(title="Profit Margin (%)", overlaying='y', side='right', showgrid=False),
        barmode='stack',
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        template="plotly_white",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

# --- Executive Insights in col3 ---
with col3:
    st.header("Executive Insights")
    st.markdown(f"""
    - Revenue grows from **${baseline_revenue:.1f}M** to **${scenario['Revenue'].iloc[-1]:.1f}M** over 10 years.  
    - Custom work decreases from **{base_custom_mix}%** to **{target_custom_mix}%** of revenue.  
    - Product work grows, requiring careful management due to lower margin ({product_margin}%) vs custom ({baseline_profit_margin}%).  
    - Profit margin trends from **{baseline_profit_margin}%** to **{scenario['ProfitMargin'].iloc[-1]:.1f}%** by Year 10.  
    """)
