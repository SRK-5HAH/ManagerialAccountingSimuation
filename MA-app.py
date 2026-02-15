import streamlit as st
import pandas as pd

# =====================================================
# PAGE SETUP
# =====================================================
st.set_page_config(page_title="Managerial Accounting Basics", layout="wide")
st.title("Managerial Accounting Basics")
st.caption("Step through formulas, load a baseline scenario, then change inputs to see the relationships.")

# =====================================================
# HELPERS
# =====================================================
def money(x):
    return f"${x:,.0f}"

def pct(x):
    return f"{x * 100:.1f}%"

def calculate_results(inputs):
    revenue = inputs["unit_price"] * inputs["net_saleable_tons"]

    var_cost_per_processed_ton = (
        inputs["energy_per_ton"] + inputs["labor_per_ton"] + inputs["other_per_ton"]
    )

    variable_cost = inputs["processed_tons"] * var_cost_per_processed_ton
    contribution = revenue - variable_cost
    ebitda = contribution - inputs["fixed_cost"]

    var_cost_per_ton = variable_cost / inputs["processed_tons"] if inputs["processed_tons"] else 0
    contribution_pct = contribution / revenue if revenue else 0
    ebitda_pct = ebitda / revenue if revenue else 0
    contrib_per_ton = contribution / inputs["processed_tons"] if inputs["processed_tons"] else 0

    return {
        "Revenue": revenue,
        "Variable Cost": variable_cost,
        "Contribution": contribution,
        "Fixed Cost": inputs["fixed_cost"],
        "EBITDA": ebitda,
        "Var Cost / Processed Ton": var_cost_per_ton,
        "Contribution / Processed Ton": contrib_per_ton,
        "Contribution %": contribution_pct,
        "EBITDA %": ebitda_pct,
        "_var_cost_per_processed_ton_component": var_cost_per_processed_ton,
    }

# Current column color is based on comparison to Original Scenario:
# - Current < Original => red
# - Current > Original => green
# - Current == Original => black
def style_comparison_table(df_raw, eps=1e-9):
    def style_row(row):
        current_val = float(row["Current"])
        original_val = float(row["Original Scenario"])
        variance_val = float(row["Variance"])

        if abs(current_val - original_val) <= eps:
            cur_style = "color: black"
        elif current_val < original_val:
            cur_style = "color: red; font-weight: 600"
        else:
            cur_style = "color: green; font-weight: 600"

        orig_style = "color: black"

        if abs(variance_val) <= eps:
            var_style = "color: black"
        elif variance_val < 0:
            var_style = "color: red; font-weight: 600"
        else:
            var_style = "color: green; font-weight: 600"

        return [cur_style, orig_style, var_style]

    styler = df_raw.style.format(money)
    styler = styler.apply(style_row, axis=1)
    return styler

# =====================================================
# DEFAULTS (integers for whole-number increments)
# =====================================================
DEFAULTS = {
    "unit_price": 200,
    "net_saleable_tons": 1000,
    "processed_tons": 1100,
    "energy_per_ton": 15,
    "labor_per_ton": 20,
    "other_per_ton": 10,
    "fixed_cost": 120000,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "step" not in st.session_state:
    st.session_state.step = 1

if "original_snapshot" not in st.session_state:
    st.session_state.original_snapshot = calculate_results(DEFAULTS.copy())

# =====================================================
# SIDEBAR CONTROLS (mobile toggle, explore mode, desktop navigation)
# =====================================================
with st.sidebar:
    st.header("View")
    mobile_view = st.toggle("Mobile view", value=True)
    explore_mode = st.toggle("Explore mode (unlock all inputs)", value=False)

    st.divider()
    st.header("Navigation")

    steps = {
        1: "1) Revenue",
        2: "2) Variable Cost",
        3: "3) Contribution",
        4: "4) Fixed Cost",
        5: "5) EBITDA",
        6: "6) Unit Economics",
    }

    # Desktop-friendly navigation stays here
    if not mobile_view:
        st.session_state.step = st.radio(
            "Choose a step",
            options=list(steps.keys()),
            format_func=lambda i: steps[i],
            index=st.session_state.step - 1,
        )

        nav1, nav2 = st.columns(2)
        with nav1:
            if st.button("◀ Prev", use_container_width=True) and st.session_state.step > 1:
                st.session_state.step -= 1
                st.rerun()
        with nav2:
            if st.button("Next ▶", use_container_width=True) and st.session_state.step < 6:
                st.session_state.step += 1
                st.rerun()

# =====================================================
# SCENARIOS (TOP)
# =====================================================
SCENARIO_TEXT = {
    "Base case": "Baseline operations. Learn how price, volume, and costs roll into Revenue, Contribution, and EBITDA.",
    "Energy spike": "Energy rates jump. Watch Variable Cost rise and EBITDA fall if price stays constant.",
    "Price pressure": "Selling price drops. Watch Revenue and margins tighten.",
    "Lower yield": "Net saleable tons drop while processed tons stay high. See how margin can shrink even when running hard.",
}

SCENARIOS = {
    "Base case": dict(DEFAULTS),
    "Energy spike": {**DEFAULTS, "energy_per_ton": 30},
    "Price pressure": {**DEFAULTS, "unit_price": 160},
    "Lower yield": {**DEFAULTS, "processed_tons": 1200, "net_saleable_tons": 950},
}

scenario_name = st.selectbox("Scenario", list(SCENARIOS.keys()))
st.info(SCENARIO_TEXT[scenario_name])

btn1, btn2 = st.columns(2)
with btn1:
    if st.button("Load scenario numbers", use_container_width=True):
        for k, v in SCENARIOS[scenario_name].items():
            st.session_state[k] = v
        st.session_state.original_snapshot = calculate_results(SCENARIOS[scenario_name].copy())
        st.rerun()

with btn2:
    if st.button("Reset to defaults", use_container_width=True):
        for k, v in DEFAULTS.items():
            st.session_state[k] = v
        st.session_state.original_snapshot = calculate_results(DEFAULTS.copy())
        st.rerun()

st.divider()

# =====================================================
# MOBILE STEP NAV (top selector)
# =====================================================
if mobile_view:
    st.session_state.step = st.selectbox(
        "Step",
        options=list(steps.keys()),
        format_func=lambda i: steps[i],
        index=st.session_state.step - 1,
    )

# =====================================================
# INPUT LOCKING
# =====================================================
def disabled_for(control_name):
    if explore_mode:
        return False

    allowed = {
        1: {"unit_price"},
        2: {"energy_per_ton", "labor_per_ton", "other_per_ton"},
        3: {"net_saleable_tons"},
        4: {"fixed_cost"},
        5: {"labor_per_ton"},
        6: {"other_per_ton", "processed_tons"},
    }
    return control_name not in allowed[st.session_state.step]

def input_label(text, key):
    return f"**{text}**" if not disabled_for(key) else text

# =====================================================
# INPUTS UI (desktop in left column, mobile in expander)
# =====================================================
def render_inputs():
    st.number_input(input_label("Unit price", "unit_price"), step=1, key="unit_price", disabled=disabled_for("unit_price"))
    st.number_input(input_label("Net saleable tons", "net_saleable_tons"), step=1, key="net_saleable_tons", disabled=disabled_for("net_saleable_tons"))
    st.number_input(input_label("Processed tons", "processed_tons"), step=1, key="processed_tons", disabled=disabled_for("processed_tons"))
    st.number_input(input_label("Energy per ton", "energy_per_ton"), step=1, key="energy_per_ton", disabled=disabled_for("energy_per_ton"))
    st.number_input(input_label("Labor per ton", "labor_per_ton"), step=1, key="labor_per_ton", disabled=disabled_for("labor_per_ton"))
    st.number_input(input_label("Other per ton", "other_per_ton"), step=1, key="other_per_ton", disabled=disabled_for("other_per_ton"))
    st.number_input(input_label("Fixed cost", "fixed_cost"), step=1000, key="fixed_cost", disabled=disabled_for("fixed_cost"))

# =====================================================
# CALCULATIONS
# =====================================================
inputs = {k: st.session_state[k] for k in DEFAULTS.keys()}
current = calculate_results(inputs)
baseline = st.session_state.original_snapshot

# =====================================================
# LESSON + RESULTS RENDER
# =====================================================
def render_lesson_and_results():
    step = st.session_state.step

    if step == 1:
        st.markdown("### Step 1: Revenue")
        st.markdown("**Revenue = Unit Price × Net Saleable Tons**")
        st.metric("Revenue", money(current["Revenue"]))

    elif step == 2:
        st.markdown("### Step 2: Variable Cost")
        st.markdown("**Variable Cost = Processed Tons × (Energy + Labor + Other)**")
        st.metric("Variable Cost", money(current["Variable Cost"]))
        st.metric("Var cost per processed ton", money(current["_var_cost_per_processed_ton_component"]))

    elif step == 3:
        st.markdown("### Step 3: Contribution")
        st.markdown("**Contribution = Revenue − Variable Cost**")
        st.metric("Contribution", money(current["Contribution"]))
        st.metric("Contribution %", pct(current["Contribution %"]))

    elif step == 4:
        st.markdown("### Step 4: EBITDA")
        st.markdown("**EBITDA = Contribution − Fixed Cost**")
        st.metric("Fixed Cost", money(current["Fixed Cost"]))
        st.metric("EBITDA", money(current["EBITDA"]))

    elif step == 5:
        st.markdown("### Step 5: Full EBITDA Formula")
        st.markdown("**EBITDA = (Unit Price × Net Saleable Tons) − (Processed Tons × Variable Cost per Ton) − Fixed Cost**")
        st.metric("EBITDA", money(current["EBITDA"]))
        st.metric("EBITDA %", pct(current["EBITDA %"]))

    elif step == 6:
        st.markdown("### Step 6: Unit Economics")
        st.markdown("**Variable Cost per Processed Ton = Variable Cost ÷ Processed Tons**")
        st.metric("Var cost / processed ton", money(current["Var Cost / Processed Ton"]))
        st.metric("Contribution / processed ton", money(current["Contribution / Processed Ton"]))

    st.divider()
    st.subheader("Full results snapshot (Current vs Original)")

    metrics = ["Revenue", "Variable Cost", "Contribution", "Fixed Cost", "EBITDA"]
    rows = []
    for m in metrics:
        cur = current[m]
        base = baseline[m]
        var = cur - base
        rows.append([cur, base, var])

    df = pd.DataFrame(rows, index=metrics, columns=["Current", "Original Scenario", "Variance"])

    # Mobile-friendly rendering
    if mobile_view:
        with st.expander("Open results table", expanded=True):
            st.dataframe(df, use_container_width=True, height=260)
    else:
        styled = style_comparison_table(df)
        st.write(styled.to_html(), unsafe_allow_html=True)

# =====================================================
# FINAL LAYOUT SWITCH
# =====================================================
if mobile_view:
    with st.expander("Inputs", expanded=True):
        render_inputs()

    st.divider()
    render_lesson_and_results()
else:
    left, right = st.columns([1, 1.6], gap="large")
    with left:
        st.subheader("Inputs")
        render_inputs()
    with right:
        render_lesson_and_results()
