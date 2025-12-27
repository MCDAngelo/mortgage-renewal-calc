import marimo

__generated_with = "0.15.5"
app = marimo.App(width="full")


@app.cell
def all_imports():
    import pandas as pd
    from canadian_mortgage_calculator import CanadianMortgageCalculator
    from mortgage_renewal import MortgageRenewalPlanner
    from renewal_scenario import RenewalScenario
    import altair as alt
    import marimo as mo
    from datetime import datetime

    # Try to load personal mortgage config (if my_mortgage.py exists)
    try:
        from my_mortgage import (
            MY_MORTGAGE_CONFIG, 
            MAX_PAYDOWN_AVAILABLE,
            RENEWAL_RATES,
            PAYDOWN_OPTIONS,
            EXTRA_ANNUAL_OPTIONS
        )
        HAS_PERSONAL_CONFIG = True
    except ImportError:
        # Use generic defaults if my_mortgage.py doesn't exist
        MY_MORTGAGE_CONFIG = {
            'original_principal': 500000,
            'annual_rate': 0.05,
            'amortization_months': 300,
            'term_months': 60,
            'start_date': datetime(2024, 1, 1),
            'mortgage_gap': (None, None),
        }
        MAX_PAYDOWN_AVAILABLE = 200000
        RENEWAL_RATES = [0.035, 0.045, 0.055]
        PAYDOWN_OPTIONS = [0, 50000, 100000, 150000]
        EXTRA_ANNUAL_OPTIONS = [0, 10000, 20000]
        HAS_PERSONAL_CONFIG = False
    return (
        CanadianMortgageCalculator,
        HAS_PERSONAL_CONFIG,
        MY_MORTGAGE_CONFIG,
        MortgageRenewalPlanner,
        PAYDOWN_OPTIONS,
        RENEWAL_RATES,
        alt,
        mo,
        pd,
    )


@app.cell
def ui_components(
    HAS_PERSONAL_CONFIG,
    MY_MORTGAGE_CONFIG,
    PAYDOWN_OPTIONS,
    RENEWAL_RATES,
    mo,
):
    # Current mortgage inputs - load from config
    orig_principal = mo.ui.number(
        label="Mortgage Principal",
        value=MY_MORTGAGE_CONFIG['original_principal'],
        start=100000,
        stop=3000000,
        step=1000,
        full_width=True,
    )
    orig_rate = mo.ui.number(
        label="Rate (%)",
        value=MY_MORTGAGE_CONFIG['annual_rate'] * 100,  # Convert to percentage
        start=1,
        stop=10,
        step=0.01,
        full_width=True,
    )
    orig_amortization = mo.ui.number(
        label="Amortization (years)",
        value=MY_MORTGAGE_CONFIG['amortization_months'] // 12,
        start=1,
        stop=30,
        step=5,
        full_width=True,
    )
    orig_term = mo.ui.number(
        label="Term (years)",
        value=MY_MORTGAGE_CONFIG['term_months'] // 12,
        start=1,
        stop=5,
        step=1,
        full_width=True,
    )

    # Handle start date
    start_date_str = MY_MORTGAGE_CONFIG['start_date'].strftime('%Y-%m-%d')
    orig_start_date = mo.ui.date(
        label="Start Date",
        value=start_date_str,
        full_width=True,
    )

    # Handle mortgage gap
    has_gap = MY_MORTGAGE_CONFIG['mortgage_gap'][0] is not None
    gap_check = mo.ui.checkbox(
        label="Did you have a gap in your mortgage?",
        value=has_gap,
    )

    if has_gap:
        gap_start_str = MY_MORTGAGE_CONFIG['mortgage_gap'][0].strftime('%Y-%m-%d')
        gap_end_str = MY_MORTGAGE_CONFIG['mortgage_gap'][1].strftime('%Y-%m-%d')
    else:
        gap_start_str = "2023-01-01"
        gap_end_str = "2023-03-01"

    orig_gap_start_date = mo.ui.date(
        label="Gap Start Date",
        value=gap_start_str,
    )
    orig_gap_end_date = mo.ui.date(
        label="Gap End Date",
        value=gap_end_str,
    )

    # Renewal scenario inputs - all as comma-separated text inputs

    # Rates input - pre-fill with config values
    default_rates_str = ', '.join([f'{r*100:.2f}' for r in RENEWAL_RATES]) if RENEWAL_RATES else '3.5, 4.0, 4.5'
    rates_input = mo.ui.text(
        label="Renewal Rates (%, comma-separated)",
        value=default_rates_str,
        full_width=True,
    )

    # Principal paydown options - pre-fill with config values (in thousands)
    default_paydowns_str = ', '.join([str(p // 1000) for p in PAYDOWN_OPTIONS]) if PAYDOWN_OPTIONS else '0, 100, 150'
    paydown_input = mo.ui.text(
        label="Principal Paydown at Renewal ($k, comma-separated)",
        value=default_paydowns_str,
        full_width=True,
    )

    # Extra monthly payment options
    extra_monthly_input = mo.ui.text(
        label="Extra Monthly Payment ($, comma-separated)",
        value="0",
        full_width=True,
    )

    # Extra annual payment percentages
    extra_annual_input = mo.ui.text(
        label="Extra Annual Payment (% of original principal, comma-separated)",
        value="0, 5, 10",
        full_width=True,
    )

    # Info message about config
    if HAS_PERSONAL_CONFIG:
        config_message = mo.md("✓ **Loaded your personal mortgage data from `my_mortgage.py`**")
    else:
        config_message = mo.md("ℹ️ Using default values. Create `my_mortgage.py` to load your personal data automatically.")
    return (
        config_message,
        extra_annual_input,
        extra_monthly_input,
        gap_check,
        orig_amortization,
        orig_gap_end_date,
        orig_gap_start_date,
        orig_principal,
        orig_rate,
        orig_start_date,
        orig_term,
        paydown_input,
        rates_input,
    )


@app.cell
def _(
    config_message,
    extra_annual_input,
    extra_monthly_input,
    gap_check,
    mo,
    orig_amortization,
    orig_gap_end_date,
    orig_gap_start_date,
    orig_principal,
    orig_rate,
    orig_start_date,
    orig_term,
    paydown_input,
    rates_input,
):
    vstack_orig = mo.vstack([
        config_message,
        mo.md("----"),
        mo.hstack([orig_principal, orig_rate, orig_start_date],
        align="stretch",
        justify="start",
                 ),
            mo.hstack([orig_amortization, orig_term],
        align="stretch",
        justify="start",
                 ),
        mo.md("----"),
        gap_check, 
        mo.hstack([orig_gap_start_date, orig_gap_end_date],
                       justify="start") if gap_check.value else ""
    ]
    )

    orig_accordion = mo.accordion({
        "**Enter your original mortgage details.**": vstack_orig,
    })

    scenario_inputs = mo.accordion({
        "**Scenario Inputs**": mo.vstack([
            mo.md("**Multiple scenarios are run using all combinations of inputs below:**"),
            rates_input,
            paydown_input,
            extra_monthly_input,
            extra_annual_input,
        ])

    })
    scenario_run_button = mo.ui.run_button(
        label="Run Analysis",
    )
    return orig_accordion, scenario_inputs, scenario_run_button


@app.cell
def form(mo, orig_accordion, scenario_inputs, scenario_run_button):
    form = mo.vstack([
        mo.md("## Canadian Mortgage Renewal Calculator"),
        mo.md("Compare mortgage renewal scenarios with different rates, paydown amounts, and extra payments."),
        orig_accordion,
        scenario_inputs,
        scenario_run_button,
    ])
    return (form,)


@app.cell
def final_layout(
    comparison_selector,
    comparison_view,
    current_mortgage,
    current_schedule,
    current_schedule_table,
    form,
    mo,
    paydown_impact_chart,
    renewal_scenarios_table,
    stage1_charts,
    stage1_paydown_selector,
    stage2_base_selector,
    stage2_charts,
    visualize_full_amortization_payments,
    visualize_mortgage_term,
):
    """Final layout assembly - pure layout logic, no computation"""

    sidebar = mo.sidebar(
        form,
        width="30rem",
    )

    # Check if data exists (not the button) to determine what to show
    if current_mortgage is not None and stage1_paydown_selector is not None:
        # Stage 1: Rate & Paydown Analysis  
        stage1_content = mo.vstack([
            mo.md("## Stage 1: Compare Rates & Pre-payment Amounts"),
            mo.md("_First, understand how interest rates and pre-payment amounts affect your mortgage_"),
            mo.md("---"),
            paydown_impact_chart,
            mo.md("---"),
            stage1_paydown_selector,
            stage1_charts,
        ])

        # Stage 2: Extra Payment Strategies
        stage2_content = mo.vstack([
            mo.md("## Stage 2: Explore Extra Payment Strategies"),
            mo.md("_Select a base scenario from Stage 1, then see how extra payments can help_"),
            mo.md("---"),
            stage2_base_selector,
            stage2_charts,
        ])

        # Comparison View
        comparison_content = mo.vstack([
            mo.md("## Compare Scenarios Side-by-Side"),
            mo.md("_Select 2-3 scenarios to compare in detail_"),
            mo.md("---"),
            comparison_selector,
            comparison_view if comparison_view is not None else mo.md(""),
        ])

        # Original Mortgage View
        original_content = mo.vstack([
            mo.md("## Your Original Mortgage"),
            current_schedule_table,
            visualize_full_amortization_payments(current_schedule),
            visualize_mortgage_term(current_mortgage, current_schedule)
        ])

        # All Scenarios Table
        all_scenarios_content = mo.vstack([
            mo.md("## All Scenarios (Detailed Table)"),
            renewal_scenarios_table
        ])

        # Create tabs
        results = mo.vstack([
            mo.md("## Results"),
            mo.ui.tabs({
                "📊 Rate & Pre-payment": stage1_content,
                "💰 Extra Payments": stage2_content,
                "⚖️ Compare Scenarios": comparison_content,
                "📋 All Scenarios": all_scenarios_content,
                "🏠 Original Mortgage": original_content,
            })
        ])
    else:
        results = mo.vstack([
            mo.md("## Welcome!"),
            mo.md("Review the inputs in the sidebar and hit **Run Analysis** to see results.")
        ])

    sidebar
    return (results,)


@app.cell
def _(
    CanadianMortgageCalculator,
    gap_check,
    mo,
    orig_amortization,
    orig_gap_end_date,
    orig_gap_start_date,
    orig_principal,
    orig_rate,
    orig_start_date,
    orig_term,
    scenario_run_button,
):
    """Generate current mortgage details - runs once when button is clicked"""

    # Stop if button not clicked yet
    if not scenario_run_button.value:
        mo.stop(False, (None, None, None))

    current_mortgage = CanadianMortgageCalculator(
        original_principal=orig_principal.value,
        annual_rate=orig_rate.value/100,
        amortization_months=orig_amortization.value*12,
        term_months=orig_term.value*12,
        start_date=orig_start_date.value,
        mortgage_gap=(orig_gap_start_date.value, orig_gap_end_date.value) if gap_check.value else (None, None)
    )

    current_schedule = current_mortgage.create_full_amortization_schedule()
    current_schedule_table = mo.ui.table(current_schedule)

    return current_mortgage, current_schedule, current_schedule_table


@app.cell
def _(
    MortgageRenewalPlanner,
    current_mortgage,
    extra_annual_input,
    extra_monthly_input,
    mo,
    orig_principal,
    paydown_input,
    rates_input,
    scenario_run_button,
):
    """
    SINGLE SOURCE OF TRUTH: Run scenario analysis once and cache results.
    This prevents redundant computations when UI elements change.
    """

    # Only run if button is clicked, otherwise stop execution
    if not scenario_run_button.value:
        mo.stop(False, None)

    # Parse rates from comma-separated input
    try:
        rates_list = [
            float(r.strip()) / 100  # Convert from percentage to decimal
            for r in rates_input.value.split(',')
            if r.strip()
        ]
    except ValueError:
        rates_list = [0.035, 0.045, 0.055]  # Fallback defaults

    # Parse paydown amounts (in thousands, convert to dollars)
    try:
        paydown_list = [
            int(float(p.strip())) * 1000
            for p in paydown_input.value.split(',')
            if p.strip()
        ]
    except ValueError:
        paydown_list = [0, 100000, 150000]  # Fallback defaults

    # Parse extra monthly payments
    try:
        extra_monthly_list = [
            int(float(m.strip()))
            for m in extra_monthly_input.value.split(',')
            if m.strip()
        ]
    except ValueError:
        extra_monthly_list = [0]  # Fallback default

    # Parse extra annual payment percentages
    try:
        extra_annual_pct_list = [
            float(a.strip())
            for a in extra_annual_input.value.split(',')
            if a.strip()
        ]
    except ValueError:
        extra_annual_pct_list = [0, 5, 10]  # Fallback defaults

    scenarios = [
            {
                'name': f'{rate*100:.2f}% + ${paydown/1000:.0f}k down + ${extra_monthly:.0f} monthly + {extra_annual_pct:.1f}% yearly',
                'new_rate': rate,
                'principal_paydown': paydown,
                'extra_monthly_payment': extra_monthly,
                'extra_annual_payment': extra_annual_pct/100 * orig_principal.value,
            }
            for rate in rates_list
            for paydown in paydown_list
            for extra_monthly in extra_monthly_list
            for extra_annual_pct in extra_annual_pct_list
        ]   

    planner = MortgageRenewalPlanner(current_mortgage)
    max_paydown = max(paydown_list) if paydown_list else 300000
    planner.scenario_analysis(scenarios, max_paydown=max_paydown)

    # CACHED RESULT - computed only once
    # Reset index to ensure unique indices for each scenario (0, 1, 2, ...)
    all_scenarios_df = planner.to_frame().reset_index(drop=True)
    renewal_scenarios_table = mo.ui.table(all_scenarios_df)

    return all_scenarios_df, renewal_scenarios_table


@app.cell
def _(all_scenarios_df, mo, scenario_run_button):
    """Stage 1: Filter cached data for base scenarios and create selector"""

    # Stop if analysis hasn't run yet
    if not scenario_run_button.value:
        mo.stop(False, (None, None))

    # Filter to base scenarios (no extra payments) from cached data
    stage1_df = all_scenarios_df[
        (all_scenarios_df['extra_monthly_payment'] == 0) & 
        (all_scenarios_df['new_extra_annual_payment'] == 0)
    ].copy()

    # Get unique paydown amounts for selector
    paydown_options = sorted(stage1_df['paydown_amount'].unique())
    paydown_options_k = [f"${int(p/1000)}k" for p in paydown_options]

    # Create selector with default to middle option
    default_idx = len(paydown_options) // 2 if paydown_options else 0
    stage1_paydown_selector = mo.ui.dropdown(
        options=dict(zip(paydown_options_k, paydown_options)),
        value=paydown_options_k[default_idx] if paydown_options_k else None,
        label="Select Pre-payment Amount"
    )
    return stage1_df, stage1_paydown_selector


@app.cell
def _(alt, mo, stage1_df, stage1_paydown_selector):
    """Stage 1: Rate comparison charts for selected paydown - PURE VISUALIZATION"""

    # Stop if no selector exists yet
    if stage1_paydown_selector is None or stage1_df is None or stage1_df.empty:
        mo.stop(False, mo.md(""))

    # Filter data for selected paydown amount (lightweight operation)
    selected_paydown = stage1_paydown_selector.value
    _filtered_df = stage1_df[stage1_df['paydown_amount'] == selected_paydown].copy()

    if _filtered_df.empty:
        mo.stop(False, mo.md("No data available for selected paydown"))

    # Format rate as percentage for display
    _filtered_df['rate_pct'] = (_filtered_df['new_rate'] * 100).round(2).astype(str) + '%'

    # Chart 1: Monthly Payment Comparison
    chart1 = alt.Chart(_filtered_df).mark_bar(size=40).encode(
        x=alt.X('rate_pct:N', title='Interest Rate', sort=None),
        y=alt.Y('new_monthly_payment:Q', title='Monthly Payment', axis=alt.Axis(format='$,.0f')),
        color=alt.Color('rate_pct:N', legend=None),
        tooltip=[
            alt.Tooltip('rate_pct:N', title='Rate'),
            alt.Tooltip('new_monthly_payment:Q', title='Monthly Payment', format='$,.2f'),
        ]
    ).properties(
        title='Monthly Payment by Interest Rate',
        width=250,
        height=200
    )

    # Chart 2: Total Interest Paid
    chart2 = alt.Chart(_filtered_df).mark_bar(size=40).encode(
        x=alt.X('rate_pct:N', title='Interest Rate', sort=None),
        y=alt.Y('total_term_interest:Q', title='Total Interest (5yr term)', axis=alt.Axis(format='$,.0f')),
        color=alt.Color('rate_pct:N', legend=None),
        tooltip=[
            alt.Tooltip('rate_pct:N', title='Rate'),
            alt.Tooltip('total_term_interest:Q', title='Total Interest', format='$,.2f'),
        ]
    ).properties(
        title='Total Interest Paid Over Term',
        width=250,
        height=200
    )

    # Chart 3: Remaining Balance
    chart3 = alt.Chart(_filtered_df).mark_bar(size=40).encode(
        x=alt.X('rate_pct:N', title='Interest Rate', sort=None),
        y=alt.Y('total_remaining:Q', title='Remaining Balance', axis=alt.Axis(format='$,.0f')),
        color=alt.Color('rate_pct:N', legend=None),
        tooltip=[
            alt.Tooltip('rate_pct:N', title='Rate'),
            alt.Tooltip('total_remaining:Q', title='Remaining Balance', format='$,.2f'),
        ]
    ).properties(
        title='Remaining Balance After Term',
        width=250,
        height=200
    )

    # Combine charts horizontally
    combined_chart = alt.hconcat(chart1, chart2, chart3).resolve_scale(
        color='independent'
    )

    stage1_charts = mo.vstack([
        mo.md(f"### Rate Comparison for ${int(selected_paydown/1000)}k Pre-payment"),
        mo.ui.altair_chart(combined_chart)
    ])

    return (stage1_charts,)


@app.cell
def _(alt, mo, stage1_df):
    """Stage 1: Paydown impact visualization across all rates - PURE VISUALIZATION"""

    # Stop if no data yet
    if stage1_df is None or stage1_df.empty:
        mo.stop(False, mo.md(""))

    # Format for display
    df_viz = stage1_df.copy()
    df_viz['rate_pct'] = (df_viz['new_rate'] * 100).round(2).astype(str) + '%'
    df_viz['paydown_k'] = (df_viz['paydown_amount'] / 1000).astype(int).astype(str) + 'k'

    # Chart: Total Interest by Paydown Amount and Rate
    _chart = alt.Chart(df_viz).mark_line(point=True).encode(
        x=alt.X('paydown_k:N', title='Pre-payment Amount', sort=None),
        y=alt.Y('total_term_interest:Q', title='Total Interest Paid', axis=alt.Axis(format='$,.0f')),
        color=alt.Color('rate_pct:N', title='Interest Rate'),
        tooltip=[
            alt.Tooltip('paydown_k:N', title='Pre-payment'),
            alt.Tooltip('rate_pct:N', title='Rate'),
            alt.Tooltip('total_term_interest:Q', title='Total Interest', format='$,.2f'),
            alt.Tooltip('new_monthly_payment:Q', title='Monthly Payment', format='$,.2f'),
        ]
    ).properties(
        title='How Pre-payment Amount Affects Total Interest',
        width=600,
        height=300
    )

    paydown_impact_chart = mo.vstack([
        mo.md("### Pre-payment Impact Across Interest Rates"),
        mo.md("_Lower is better - shows how much you can save with different pre-payment amounts_"),
        mo.ui.altair_chart(_chart)
    ])

    return (paydown_impact_chart,)


@app.cell
def _(mo, scenario_run_button, stage1_df):
    """Stage 2: Base scenario selector for extra payment exploration"""

    # Stop if no data yet
    if not scenario_run_button.value or stage1_df is None or stage1_df.empty:
        mo.stop(False, None)

    # Create options from base scenarios
    _scenario_options = {}
    for _, _row in stage1_df.iterrows():
        _rate_pct = _row['new_rate'] * 100
        _paydown_k = int(_row['paydown_amount'] / 1000)
        _label = f"{_rate_pct:.2f}% rate + ${_paydown_k}k pre-payment"
        _scenario_options[_label] = {
            'rate': _row['new_rate'],
            'paydown': _row['paydown_amount'],
            'monthly_payment': _row['new_monthly_payment'],
            'base_interest': _row['total_term_interest']
        }

    # Default to first option
    default_key = list(_scenario_options.keys())[0] if _scenario_options else None

    stage2_base_selector = mo.ui.dropdown(
        options=_scenario_options,
        value=default_key,
        label="Select Base Scenario"
    )
    return (stage2_base_selector,)


@app.cell
def _(all_scenarios_df, alt, mo, stage2_base_selector):
    """Stage 2: Extra payment impact visualization - PURE VISUALIZATION"""

    # Stop if no selector or value
    if stage2_base_selector is None or stage2_base_selector.value is None:
        mo.stop(False, mo.md(""))

    # Filter cached data to scenarios matching the selected base rate and paydown
    base_rate = stage2_base_selector.value['rate']
    base_paydown = stage2_base_selector.value['paydown']

    filtered_df = all_scenarios_df[
        (all_scenarios_df['new_rate'] == base_rate) & 
        (all_scenarios_df['paydown_amount'] == base_paydown)
    ].copy()

    if filtered_df.empty:
        mo.stop(False, mo.md("No extra payment scenarios available"))

    # Separate by extra payment type
    monthly_df = filtered_df[
        (filtered_df['extra_monthly_payment'] > 0) & 
        (filtered_df['new_extra_annual_payment'] == 0)
    ].copy()

    annual_df = filtered_df[
        (filtered_df['extra_monthly_payment'] == 0) & 
        (filtered_df['new_extra_annual_payment'] > 0)
    ].copy()

    charts = []

    # Chart 1: Extra Monthly Payment Impact
    if not monthly_df.empty:
        monthly_df = monthly_df.sort_values('extra_monthly_payment')
        chart_monthly = alt.Chart(monthly_df).mark_line(point=True, color='#1f77b4').encode(
            x=alt.X('extra_monthly_payment:Q', title='Extra Monthly Payment ($)'),
            y=alt.Y('total_term_interest:Q', title='Total Interest Paid', axis=alt.Axis(format='$,.0f')),
            tooltip=[
                alt.Tooltip('extra_monthly_payment:Q', title='Extra Monthly', format='$,.0f'),
                alt.Tooltip('total_term_interest:Q', title='Total Interest', format='$,.2f'),
                alt.Tooltip('payoff_time_months:Q', title='Payoff Time (months)'),
            ]
        ).properties(
            title='Impact of Extra Monthly Payments',
            width=400,
            height=250
        )
        charts.append(mo.ui.altair_chart(chart_monthly))

    # Chart 2: Anniversary Payment Impact
    if not annual_df.empty:
        annual_df = annual_df.sort_values('new_extra_annual_payment')
        annual_df['annual_pct'] = (annual_df['new_extra_annual_payment'] / base_paydown * 100).round(1)

        chart_annual = alt.Chart(annual_df).mark_line(point=True, color='#ff7f0e').encode(
            x=alt.X('new_extra_annual_payment:Q', title='Extra Annual Payment ($)', axis=alt.Axis(format='$,.0f')),
            y=alt.Y('total_term_interest:Q', title='Total Interest Paid', axis=alt.Axis(format='$,.0f')),
            tooltip=[
                alt.Tooltip('new_extra_annual_payment:Q', title='Extra Annual', format='$,.0f'),
                alt.Tooltip('total_term_interest:Q', title='Total Interest', format='$,.2f'),
                alt.Tooltip('payoff_time_months:Q', title='Payoff Time (months)'),
            ]
        ).properties(
            title='Impact of Anniversary Payments',
            width=400,
            height=250
        )
        charts.append(mo.ui.altair_chart(chart_annual))

    if not charts:
        mo.stop(False, mo.md("_No extra payment scenarios to display. Add extra monthly or annual payment options in the inputs._"))

    base_interest = stage2_base_selector.value['base_interest']

    stage2_charts = mo.vstack([
        mo.md(f"### Extra Payment Strategies"),
        mo.md(f"**Base scenario interest:** ${base_interest:,.2f}"),
        mo.md("_See how extra payments reduce your total interest cost_"),
        *charts
    ])

    return filtered_df, stage2_charts


@app.cell
def _(all_scenarios_df, mo, scenario_run_button):
    """Scenario comparison: Multi-select for side-by-side comparison"""

    # Stop if no data yet
    if not scenario_run_button.value:
        mo.stop(False, None)

    # Create scenario labels from cached data
    scenario_options = {}
    for idx, row in all_scenarios_df.iterrows():
        rate_pct = row['new_rate'] * 100
        paydown_k = int(row['paydown_amount'] / 1000)
        monthly = int(row['extra_monthly_payment'])
        annual = int(row['new_extra_annual_payment'])

        label = f"{rate_pct:.2f}% + ${paydown_k}k"
        if monthly > 0:
            label += f" + ${monthly}/mo"
        if annual > 0:
            label += f" + ${annual}/yr"

        scenario_options[label] = idx

    # Multi-select for comparison (limit to 3)
    comparison_selector = mo.ui.multiselect(
        options=scenario_options,
        label="Select up to 3 scenarios to compare"
    )
    return (comparison_selector,)


@app.cell
def _(all_scenarios_df, alt, comparison_selector, mo, pd):
    """Scenario comparison: Side-by-side visualization - PURE VISUALIZATION"""
    comparison_view = None

    # Stop if no selector or no values selected
    if comparison_selector is None or not comparison_selector.value:
        mo.stop(False, mo.md("_Select 2-3 scenarios above to compare them side-by-side_"))

    if len(comparison_selector.value) > 3:
        mo.stop(False, mo.md("⚠️ Please select no more than 3 scenarios for comparison"))

    if 1 <= len(comparison_selector.value) <= 3:
        # Get selected scenarios from cached data
        selected_indices = list(comparison_selector.value)
        
        # Filter to only selected scenarios using index-based filtering
        comparison_df = all_scenarios_df[all_scenarios_df.index.isin(selected_indices)].copy()
    
        # Create scenario labels
        comparison_df['scenario_label'] = comparison_df.apply(
            lambda row: f"{row['new_rate']*100:.2f}% + ${int(row['paydown_amount']/1000)}k" + 
                       (f" + ${int(row['extra_monthly_payment'])}/mo" if row['extra_monthly_payment'] > 0 else "") +
                       (f" + ${int(row['new_extra_annual_payment'])}/yr" if row['new_extra_annual_payment'] > 0 else ""),
            axis=1
        )
    
        # Create comparison table - reset index to ensure clean display
        table_data = comparison_df[[
            'scenario_label',
            'new_monthly_payment',
            'total_term_interest',
            'total_remaining',
            'payoff_time_months'
        ]].copy().reset_index(drop=True)
    
        table_data.columns = [
            'Scenario',
            'Monthly Payment',
            'Total Interest (5yr)',
            'Remaining Balance',
            'Payoff Time (months)'
        ]
    
        # Format currency columns
        for col in ['Monthly Payment', 'Total Interest (5yr)', 'Remaining Balance']:
            table_data[col] = table_data[col].apply(lambda x: f"${x:,.2f}")
    
        # Prepare data for charts
        metrics_df = comparison_df[['scenario_label', 'new_monthly_payment', 'total_term_interest', 'total_remaining']].copy()
    
        # Melt for visualization
        melted_df = pd.melt(
            metrics_df,
            id_vars=['scenario_label'],
            value_vars=['new_monthly_payment', 'total_term_interest', 'total_remaining'],
            var_name='metric',
            value_name='amount'
        )
    
        # Rename metrics for display
        metric_names = {
            'new_monthly_payment': 'Monthly Payment',
            'total_term_interest': 'Total Interest',
            'total_remaining': 'Remaining Balance'
        }
        melted_df['metric'] = melted_df['metric'].map(metric_names)
    
        # Create grouped bar chart
        chart = alt.Chart(melted_df).mark_bar().encode(
            x=alt.X('scenario_label:N', title=None, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('amount:Q', title='Amount ($)', axis=alt.Axis(format='$,.0f')),
            color=alt.Color('scenario_label:N', title='Scenario'),
            column=alt.Column('metric:N', title=None),
            tooltip=[
                alt.Tooltip('scenario_label:N', title='Scenario'),
                alt.Tooltip('amount:Q', title='Amount', format='$,.2f')
            ]
        ).properties(
            width=180,
            height=250
        ).resolve_scale(
            y='independent'
        )
    
        comparison_view = mo.vstack([
            mo.md(f"### Side-by-Side Comparison ({len(comparison_df)} scenarios selected)"),
            mo.ui.table(table_data, selection=None),
            mo.md("#### Visual Comparison"),
            mo.ui.altair_chart(chart)
        ])

    return (comparison_view,)


@app.cell
def _(alt, mo, pd):
    def visualize_full_amortization_payments(sched):
        sched = sched[["Date", "Principal_Payment", "Interest_Payment"]]
        sched.columns = ["Date", "principal", "interest"]
        pivot_sched = pd.melt(
            sched,
            id_vars="Date",
            value_vars=["principal", "interest"],
            var_name="payment_type",
            value_name="amount"
        )
        pivot_sched["Date"] = pd.to_datetime(pivot_sched["Date"])
        pivot_sched["payment_type"] = pivot_sched["payment_type"].astype(str)
        plt = alt.Chart(pivot_sched).mark_bar().encode(
            alt.X("year(Date):T").axis(),
            alt.Y("sum(amount):Q").axis(format='$').title('Payment Amount'),
            color="payment_type:N"
        )
        return mo.ui.altair_chart(plt)
    return (visualize_full_amortization_payments,)


@app.cell
def _(alt, mo, pd):
    def visualize_mortgage_term(m, sched):
        sched = sched.iloc[:m.term_months][["Date", "Ending_Balance"]]
        sched["Date"] = pd.to_datetime(sched["Date"])
        sched["Ending_Balance"] = round(sched["Ending_Balance"])
        plt = alt.Chart(sched).mark_line().encode(
            alt.X("yearmonth(Date):T").axis().title("Month"),
            alt.Y("Ending_Balance:Q").axis(format='$').title('Ending Balance')
        )
        return mo.ui.altair_chart(plt)
    return (visualize_mortgage_term,)


@app.cell
def _(results):
    results
    return


if __name__ == "__main__":
    app.run()
