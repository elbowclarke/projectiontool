# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Branding ---
st.set_page_config(page_title="BWC 10-Year Forecast", layout="wide", page_icon=":house:")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Roboto', sans-serif; }
    .css-18e3th9 { background-color: #f7f7f7; }
    .stButton>button { background-color: #0b3d91; color: white; }
    </style>
    <img src="https://www.bensonwood.com/wp-content/uploads/2023/03/bensonwood-logo.png" width="250">
    """,
    unsafe_allow_html=True
)

# --- Session state ---
if "saved" not in st.session_state:
    st.session_state.saved = {}

# --- Layout ---
left_col, center_col, right_col = st.columns([2, 4, 2])

# --- Left Column: Assumptions ---
with left_col:
    st.header("Assumptions & Controls")
    starting_custom_mix = st.slider("Starting Custom Work Mix (%)", 40, 80, 60, step=5,
                                    help="Current % of revenue from custom work (rest is product work).")
    target_custom_mix = st.slider("Target Custom Work Mix (%)", 40, 80, 50, step=5,
                                  help="Target % of revenue from custom work over 10 years.")
    years = st.slider("Projection Period (years)", 5, 15, 10, step=1)
    
    price_custom = st.number_input("Avg Custom Price ($)", 200000, 3000000, 750000, step=50000)
    price_product = st.number_input("Avg Product Price ($)", 100000, 1500000, 350000, step=25000)
    
    cost_custom = st.number_input("Avg Custom Cost ($)", 100000, 2500000, 500000, step=25000)
    cost_product = st.number_input("Avg Product Cost ($)", 50000, 1000000, 250000, step=25000)
    
    fixed_costs = st.number_input("Fixed Costs ($)", 500000, 5000000, 1200000, step=50000)
    
    growth_rate_product = st.slider("Annual Volume Growth for Product Work (%)", 0, 50, 10, step=1,
                                   help="How much product work can grow each year.")

# --- Calculations ---
years_list = list(range(1, years + 1))
custom_mix_list = [starting_custom_mix - (starting_custom_mix - target_custom_mix) * (i/(years-1)) for i in range(years)]
product_mix_list = [100 - cm for cm in custom_mix_list]

volume_custom = [50 for _ in years_list]  # static example, can be dynamic
volume_product = [50 * ((1 + growth_rate_product/100)**i) for i in range(years)]

price_per_unit_list = [pc*cm/100 + pp*pm/100 for pc, pp, cm, pm in zip([price_custom]*years, [price_product]*years, custom_mix_list, product_mix_list)]
cost_per_unit_list = [cc*cm/100 + cp*pm/100 for cc, cp, cm, pm in zip([cost_custom]*years, [cost_product]*years, custom_mix_list, product_mix_list)]

margin_per_unit_list = [ppu - cpu for ppu, cpu in zip(price_per_unit_list, cost_per_unit_list)]
revenue_list = [vc*price_custom + vp*price_product for vc, vp in zip(volume_custom, volume_product)]
total_costs_list = [vc*cost_custom + vp*cost_product + fixed_costs for vc, vp in zip(volume_custom, volume_product)]
profit_list = [rev - tc for rev, tc in zip(revenue_list, total_costs_list)]

break_even_volume_product = [(fixed_costs + vc*(price_custom-cost_custom) - vc*(price_custom-cost_custom))/max(price_product-cost_product,1)
                             for vc in volume_custom]  # simplistic illustration

df = pd.DataFrame({
    "Year": years_list,
    "Custom Mix (%)": custom_mix_list,
    "Product Mix (%)": product_mix_list,
    "Revenue": revenue_list,
    "Profit": profit_list,
    "Margin per Unit": margin_per_unit_list,
    "Break-Even Volume Product": break_even_volume_product,
    "Volume Custom": volume_custom,
    "Volume Product": volume_product
})

# --- Center Column: Charts ---
with center_col:
    st.header("10-Year Projection")
    # Revenue & Profit
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["Year"], y=df["Revenue"], name="Revenue", marker_color="#0b3d91"))
    fig.add_trace(go.Bar(x=df["Year"], y=df["Profit"], name="Profit", marker_color="#f27c00"))
    fig.update_layout(barmode="group", title="Revenue vs Profit Over Time",
                      yaxis_title="USD ($)", xaxis_title="Year")
    st.plotly_chart(fig, use_container_width=True)
    
    # Product Mix Evolution
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df["Year"], y=df["Custom Mix (%)"], mode='lines+markers', name='Custom Mix', line=dict(color="#0b3d91")))
    fig2.add_trace(go.Scatter(x=df["Year"], y=df["Product Mix (%)"], mode='lines+markers', name='Product Mix', line=dict(color="#f27c00")))
    fig2.update_layout(title="Revenue Mix Over Time", yaxis_title="Percent (%)", xaxis_title="Year")
    st.plotly_chart(fig2, use_container_width=True)

    # Volume vs Break-Even
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df["Year"], y=df["Volume Product"], mode='lines+markers', name='Product Volume', line=dict(color="#0b3d91")))
    fig3.add_trace(go.Scatter(x=df["Year"], y=df["Break-Even Volume Product"], mode='lines+markers', name='Break-Even Volume', line=dict(color="red", dash='dash')))
    fig3.update_layout(title="Product Volume vs Break-Even Volume", yaxis_title="Units", xaxis_title="Year")
    st.plotly_chart(fig3, use_container_width=True)

# --- Right Column: Executive Insights ---
with right_col:
    st.header("Executive Insights")
    latest_year = df.iloc[-1]
    st.write(f"**Final Year Mix:** {latest_year['Custom Mix (%)']:.0f}% Custom / {latest_year['Product Mix (%)']:.0f}% Product")
    st.write(f"**Revenue:** ${latest_year['Revenue']:,.0f}")
    st.write(f"**Profit:** ${latest_year['Profit']:,.0f}")
    if latest_year['Profit'] < 0:
        st.warning("Profit is negative in final year — consider increasing margins or controlling volume growth.")
    elif latest_year['Volume Product'] < latest_year['Break-Even Volume Product']:
        st.info("Product volume is below break-even — must increase to cover fixed costs.")
    else:
        st.success("Final year scenario profitable and above break-even.")

# --- Save scenario ---
st.header("Saved Scenarios")
scenario_name = st.text_input("Scenario Name", value=f"Scenario {len(st.session_state.saved)+1}")
if st.button("Save Scenario"):
    st.session_state.saved[scenario_name] = df.to_dict()
    st.success(f"Scenario '{scenario_name}' saved.")
    
# Tabs for saved scenarios
tab_labels = list(st.session_state.saved.keys())
if tab_labels:
    tabs = st.tabs(tab_labels)
    for label, tab in zip(tab_labels, tabs):
        with tab:
            st.write(f"### Saved Scenario: {label}")
            st.dataframe(pd.DataFrame(st.session_state.saved[label]))
