import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Bensonwood Revenue & Profit Dashboard with Insights")

st.title("Bensonwood Revenue & Profit Dashboard with Scenario Insights")

# -----------------------------
# Sidebar: Scenario Selection
# -----------------------------
st.sidebar.header("Scenario Settings")
num_scenarios = st.sidebar.number_input("Number of Scenarios to Compare", 1, 5, 2)

scenarios = []
for s in range(num_scenarios):
    st.sidebar.markdown(f"### Scenario {s+1}")
    scenario = {}
    scenario['name'] = st.sidebar.text_input(f"Scenario {s+1} Name", f"Scenario {s+1}", key=f"name{s}")
    scenario['starting_mix_custom'] = st.sidebar.slider(f"Starting Custom % (Scenario {s+1})", 50, 100, 60, 5, key=f"smc{s}")
    scenario['target_mix_custom'] = st.sidebar.slider(f"Target Custom % (Scenario {s+1})", 0, 100, 50, 5, key=f"tmc{s}")
    scenario['transition_years'] = st.sidebar.slider(f"Transition Years (Scenario {s+1})", 1, 10, 5, key=f"ty{s}")
    scenario['custom_units'] = st.sidebar.number_input(f"Annual Custom Units (Scenario {s+1})", 1, 100, 20, key=f"cu{s}")
    scenario['product_units'] = st.sidebar.number_input(f"Annual Product Units (Scenario {s+1})", 1, 100, 15, key=f"pu{s}")
    scenario['custom_price'] = st.sidebar.number_input(f"Custom Price $M (Scenario {s+1})", 0.1, 10.0, 1.8, 0.05, key=f"cp{s}")
    scenario['product_price'] = st.sidebar.number_input(f"Product Price $M (Scenario {s+1})", 0.1, 5.0, 0.65, 0.01, key=f"pp{s}")
    scenario['custom_margin'] = st.sidebar.slider(f"Custom Margin % (Scenario {s+1})", 0, 100, 25, key=f"cm{s}")
    scenario['product_margin'] = st.sidebar.slider(f"Product Margin % (Scenario {s+1})", 0, 100, 20, key=f"pm{s}")
    scenario['design_margin'] = st.sidebar.slider(f"Design Margin % (Scenario {s+1})", 0, 100, 50, key=f"dm{s}")
    scenario['premium_adoption'] = st.sidebar.slider(f"Premium Adoption % (Scenario {s+1})", 0, 100, 40, key=f"pa{s}")
    scenario['custom_design_price'] = st.sidebar.number_input(f"Custom Design $K (Scenario {s+1})", 0, 200, 45, 1, key=f"cdp{s}")*1000
    scenario['product_design_price'] = st.sidebar.number_input(f"Product Design $K (Scenario {s+1})", 0, 100, 18, 1, key=f"pdp{s}")*1000
    scenario['max_custom_capacity'] = st.sidebar.number_input(f"Max Custom Units (Scenario {s+1})", 1, 100, 25, key=f"mcc{s}")
    scenario['max_product_capacity'] = st.sidebar.number_input(f"Max Product Units (Scenario {s+1})", 1, 100, 25, key=f"mpc{s}")
    scenarios.append(scenario)

# -----------------------------
# Function: Run Scenario Calculations
# -----------------------------
def run_scenario(s):
    years = np.arange(1, s['transition_years'] + 1)
    custom_mix = np.linspace(s['starting_mix_custom']/100, s['target_mix_custom']/100, s['transition_years'])
    product_mix = 1 - custom_mix

    total_units = np.minimum(s['custom_units'] + s['product_units'], s['max_custom_capacity'] + s['max_product_capacity'])
    custom_units_final = np.round(custom_mix * total_units)
    product_units_final = np.round(product_mix * total_units)

    # Revenue
    custom_revenue = custom_units_final * s['custom_price'] * 1e6
    product_revenue = product_units_final * s['product_price'] * 1e6
    design_revenue = (custom_units_final + product_units_final) * s['premium_adoption']/100 * \
                     (s['custom_design_price'] * custom_units_final/(custom_units_final+product_units_final) + \
                      s['product_design_price'] * product_units_final/(custom_units_final+product_units_final))
    total_revenue = custom_revenue + product_revenue + design_revenue

    # Profit
    custom_profit = custom_revenue * s['custom_margin']/100
    product_profit = product_revenue * s['product_margin']/100
    design_profit = design_revenue * s['design_margin']/100
    total_profit = custom_profit + product_profit + design_profit

    # Baseline profit
    baseline_custom_units = np.minimum(s['custom_units'], s['max_custom_capacity'])
    baseline_product_units = np.minimum(s['product_units'], s['max_product_capacity'])
    baseline_custom_profit = baseline_custom_units * s['custom_price']*1e6 * s['custom_margin']/100
    baseline_product_profit = baseline_product_units * s['product_price']*1e6 * s['product_margin']/100
    baseline_design_profit = (baseline_custom_units + baseline_product_units) * s['premium_adoption']/100 * \
                             (s['custom_design_price']*baseline_custom_units/(baseline_custom_units+baseline_product_units) + \
                              s['product_design_price']*baseline_product_units/(baseline_custom_units+baseline_product_units)) * s['design_margin']/100
    baseline_profit = baseline_custom_profit + baseline_product_profit + baseline_design_profit

    # Required additional product units
    profit_shortfall = np.maximum(baseline_profit - total_profit, 0)
    profit_per_product_unit = s['product_price']*1e6*s['product_margin']/100 + s['product_design_price']*s['design_margin']/100*s['premium_adoption']/100
    required_additional_product_units = profit_shortfall / profit_per_product_unit

    # Capacity warnings
    capacity_warnings = []
    for i in range(len(years)):
        warnings = []
        if custom_units_final[i] > s['max_custom_capacity']:
            warnings.append(f"Custom units exceed capacity ({custom_units_final[i]} > {s['max_custom_capacity']})")
        if product_units_final[i] + required_additional_product_units[i] > s['max_product_capacity']:
            warnings.append(f"Required product units exceed capacity ({product_units_final[i]+required_additional_product_units[i]:.1f} > {s['max_product_capacity']})")
        if profit_shortfall[i] > 0:
            warnings.append(f"Profit shortfall: ${profit_shortfall[i]/1e6:.1f}M")
        capacity_warnings.append(warnings)
    return {
        'years': years,
        'custom_units_final': custom_units_final,
        'product_units_final': product_units_final,
        'total_profit': total_profit,
        'baseline_profit': baseline_profit,
        'required_additional_product_units': required_additional_product_units,
        'warnings': capacity_warnings
    }

# -----------------------------
# Run Scenarios & Display Insights
# -----------------------------
for i, s in enumerate(scenarios):
    st.subheader(f"Scenario: {s['name']}")
    res = run_scenario(s)

    # Revenue & Profit Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=res['years'], y=res['total_profit']/1e6, mode='lines+markers', name='Total Profit ($M)'))
    fig.add_hline(y=res['baseline_profit']/1e6, line_dash="dash", line_color="red", annotation_text="Baseline Profit", annotation_position="top right")
    st.plotly_chart(fig, use_container_width=True)

    # Required Additional Product Units
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=res['years'], y=res['required_additional_product_units'], name='Required Additional Product Units', marker_color='orange'))
    st.plotly_chart(fig2, use_container_width=True)

    # Units Comparison
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=res['years'], y=res['custom_units_final'], name='Custom Units', marker_color='blue'))
    fig3.add_trace(go.Bar(x=res['years'], y=res['product_units_final'], name='Product Units', marker_color='green', opacity=0.7))
    st.plotly_chart(fig3, use_container_width=True)

    # -----------------------------
    # Insight Panel
    # -----------------------------
    st.markdown("**Scenario Insights & Warnings**")
    for year, warnings in zip(res['years'], res['warnings']):
        st.markdown(f"**Year {year}:**")
        if warnings:
            for w in warnings:
                st.markdown(f"- ⚠ {w}")
        else:
            st.markdown("- ✅ All targets met, profit maintained within capacity")
