# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Branding ---
st.set_page_config(page_title="BWC Forecaster", layout="wide", page_icon=":house:")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Roboto', sans-serif;
    }
    .css-18e3th9 {
        background-color: #f7f7f7;
    }
    .stButton>button {
        background-color: #0b3d91;
        color: white;
    }
    </style>
    <img src="https://www.bensonwood.com/wp-content/uploads/2023/03/bensonwood-logo.png" width="250">
    """,
    unsafe_allow_html=True
)

# --- Session state for saved scenarios ---
if "saved" not in st.session_state:
    st.session_state.saved = {}

# --- Layout ---
left_col, center_col, right_col = st.columns([2, 4, 2])

# --- Left Column: Scenario Controls ---
with left_col:
    st.header("Scenario Controls")
    volume = st.slider("Volume (units)", 50, 1000, 300, help="Number of homes/products planned in this scenario.")
    product_mix = st.select_slider(
        "Product Mix",
        options=["High Margin", "Medium Margin", "Low Margin"],
        help="Shift between high-margin and low-margin products."
    )
    price_per_unit = st.slider("Average Price per Unit ($)", 100000, 2000000, 500000, step=50000,
                               help="Average selling price per unit/product.")
    cost_per_unit = st.slider("Average Cost per Unit ($)", 50000, 1500000, 300000, step=50000,
                              help="Average cost per unit/product including materials and labor.")
    fixed_costs = st.slider("Fixed Costs ($)", 500000, 5000000, 1000000, step=50000,
                            help="Total fixed costs for operations.")

# --- Calculations ---
margin_per_unit = price_per_unit - cost_per_unit
total_contribution = margin_per_unit * volume
profit = total_contribution - fixed_costs
break_even_volume = fixed_costs / max(margin_per_unit, 1)

# --- Center Column: Charts ---
with center_col:
    st.header("Financial Forecast Dashboard")

    # Profit vs Volume with animation effect
    x_vals = list(range(0, int(break_even_volume*2), int(max(break_even_volume/20,1))))
    y_vals = [margin_per_unit*v - fixed_costs for v in x_vals]

    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='lines+markers',
        name='Profit Curve',
        hovertemplate="Volume: %{x}<br>Profit: $%{y:,.0f}<extra></extra>",
        line=dict(color="#0b3d91", width=3)
    ))
    fig.add_trace(go.Scatter(
        x=[break_even_volume, break_even_volume],
        y=[min(y_vals), 0],
        mode='lines',
        name='Break-Even',
        line=dict(color="red", dash='dash'),
        hovertemplate="Break-even at %{x:,.0f} units<extra></extra>"
    ))
    fig.update_layout(height=500, title_text="Profit vs Volume", xaxis_title="Volume", yaxis_title="Profit ($)",
                      transition={'duration': 500, 'easing': 'cubic-in-out'})
    st.plotly_chart(fig, use_container_width=True)

    # Margin per unit gauge
    fig2 = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=margin_per_unit,
        delta={'reference': 0, 'position': "top"},
        title={'text': "Margin per Unit ($)"},
        gauge={'axis': {'range': [0, price_per_unit]}, 'bar': {'color': "#0b3d91"}}
    ))
    st.plotly_chart(fig2, use_container_width=True)

# --- Right Column: Executive Insights ---
with right_col:
    st.header("Executive Insights")
    st.write(f"**Scenario:** {product_mix}")
    st.write(f"**Total Profit:** ${profit:,.0f}")
    st.write(f"**Break-Even Volume:** {break_even_volume:,.0f} units")
    if margin_per_unit <= 0:
        st.warning("Margin per unit is zero or negative. Consider increasing price or reducing costs.")
    elif volume < break_even_volume:
        st.info("Current volume is below break-even. Increase volume or adjust mix.")
    else:
        st.success("Scenario is profitable above break-even volume.")

# --- Tabs for saved scenarios ---
st.header("Saved Scenarios")
tab_labels = list(st.session_state.saved.keys())
tabs = st.tabs(tab_labels if tab_labels else ["No saved scenarios yet"])

for label, tab in zip(tab_labels, tabs):
    with tab:
        st.write(f"### Saved Scenario: {label}")
        st.json(st.session_state.saved[label])

# --- Save current scenario ---
st.write("---")
scenario_name = st.text_input("Enter scenario name to save:", value=f"Scenario {len(st.session_state.saved)+1}")
if st.button("Save Current Scenario"):
    if scenario_name:
        st.session_state.saved[scenario_name] = {
            "volume": volume,
            "product_mix": product_mix,
            "price_per_unit": price_per_unit,
            "cost_per_unit": cost_per_unit,
            "fixed_costs": fixed_costs,
            "margin_per_unit": margin_per_unit,
            "profit": profit,
            "break_even_volume": break_even_volume
        }
        st.success(f"Scenario '{scenario_name}' saved and available in tabs.")
