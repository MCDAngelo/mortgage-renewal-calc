import marimo

__generated_with = "0.15.5"
app = marimo.App(width="full")


@app.cell
def all_imports():
    import pandas as pd
    from canadian_mortgage_calculator import CanadianMortgageCalculator
    from mortgage_renewal import MortgageRenewalPlanner
    import marimo as mo
    from datetime import datetime

    # Try to load personal mortgage config (if my_mortgage.py exists)
    try:
        from my_mortgage import MY_MORTGAGE_CONFIG, DEFAULT_SCENARIO_CONFIGS, MAX_PAYDOWN_AVAILABLE
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
        DEFAULT_SCENARIO_CONFIGS = {f"Scenario {i+1}": {} for i in range(5)}
        HAS_PERSONAL_CONFIG = False
        MAX_PAYDOWN_AVAILABLE = 100000
    return (
        CanadianMortgageCalculator,
        DEFAULT_SCENARIO_CONFIGS,
        HAS_PERSONAL_CONFIG,
        MAX_PAYDOWN_AVAILABLE,
        MY_MORTGAGE_CONFIG,
        MortgageRenewalPlanner,
        mo,
        pd,
    )


@app.cell
def ui_components(HAS_PERSONAL_CONFIG, MY_MORTGAGE_CONFIG, mo):
    """Original mortgage inputs"""
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
        value=MY_MORTGAGE_CONFIG['annual_rate'] * 100,
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

    start_date_str = MY_MORTGAGE_CONFIG['start_date'].strftime('%Y-%m-%d')
    orig_start_date = mo.ui.date(
        label="Start Date",
        value=start_date_str,
        full_width=True,
    )

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

    if HAS_PERSONAL_CONFIG:
        config_message = mo.md("✓ **Loaded your personal mortgage data from `my_mortgage.py`**")
    else:
        config_message = mo.md("ℹ️ Using default values. Create `my_mortgage.py` to load your personal data automatically.")
    return (
        config_message,
        gap_check,
        orig_amortization,
        orig_gap_end_date,
        orig_gap_start_date,
        orig_principal,
        orig_rate,
        orig_start_date,
        orig_term,
    )


@app.cell
def original_mortgage_form(
    config_message,
    gap_check,
    mo,
    orig_amortization,
    orig_gap_end_date,
    orig_gap_start_date,
    orig_principal,
    orig_rate,
    orig_start_date,
    orig_term,
):
    """Original mortgage setup form"""
    orig_form = mo.vstack([
        mo.md("## Your Original Mortgage"),
        config_message,
        mo.md("---"),
        mo.hstack([orig_principal, orig_rate, orig_start_date], justify="start"),
        mo.hstack([orig_amortization, orig_term], justify="start"),
        mo.md("---"),
        gap_check, 
        mo.hstack([orig_gap_start_date, orig_gap_end_date], justify="start") if gap_check.value else mo.md(""),
    ])
    return (orig_form,)


@app.cell
def calculate_current_mortgage(
    CanadianMortgageCalculator,
    format_currency,
    gap_check,
    mo,
    orig_amortization,
    orig_gap_end_date,
    orig_gap_start_date,
    orig_principal,
    orig_rate,
    orig_start_date,
    orig_term,
):
    """Calculate current mortgage automatically (no button needed)"""
    current_mortgage = CanadianMortgageCalculator(
        original_principal=orig_principal.value,
        annual_rate=orig_rate.value / 100,
        amortization_months=orig_amortization.value * 12,
        term_months=orig_term.value * 12,
        start_date=orig_start_date.value,
        mortgage_gap=(orig_gap_start_date.value, orig_gap_end_date.value) if gap_check.value else (None, None)
    )

    # Calculate balance at renewal by creating schedule
    _ = current_mortgage.create_full_amortization_schedule()
    balance_at_renewal = current_mortgage.balance_at_renewal

    # Calculate remaining amortization (total - term already completed)
    remaining_amortization = current_mortgage.amortization_months - current_mortgage.term_months

    current_mortgage_display = mo.vstack([
        mo.md("## Original Mortgage Details"),
        mo.md(f"Monthly Payment: {format_currency(current_mortgage.monthly_payment)}"),
        mo.md(f"Total Principal Paid: {format_currency(current_mortgage.total_term_principal)}"),
        mo.md(f"Total Interest Paid: {format_currency(current_mortgage.total_term_interest)}"),
        mo.md(f"Balance at Renewal: {format_currency(balance_at_renewal)}"),
    ])
    return (
        balance_at_renewal,
        current_mortgage,
        current_mortgage_display,
        remaining_amortization,
    )


@app.cell
def helper_functions_and_defaults(
    MAX_PAYDOWN_AVAILABLE,
    MortgageRenewalPlanner,
):
    """Helper functions for formatting"""

    ui_configs = {
        "rate_input": {
            "label": "Rate (%)",
            "value": 3.5,
            "start": 1.0,
            "stop": 6.0,
            "step": 0.01,
        },
        "rate_type_input": {
            "label": "Type:",
            "options": {"Fixed": "fixed", "Variable": "variable"},
            "value": "Fixed",
        },
        "paydown_input": {
            "label": "Paydown ($)",
            "start": 0,
            "stop": 300000,
            "step": 5000,
            "value": 50000,
        },
        "amortization_input": {
            "label": "Amortization (Yrs):",
            "options": [10, 15, 20, 25],
            "value": 25,
        },
        "double_payment_input": {
            "label": "Double-up Monthly Payments",
            "value": False,
        },
        "annual_payment_input": {
            "label": "Anniv. Amt",
            "value": 0,
            "start": 0,
            "stop": 60000,
            "step": 1000,
        },
    }

    def format_currency(value):
        """Format value as currency"""
        return f"${value:,.0f}"

    def get_risk_badge(risk_score, rate_type="variable"):
        """Get risk badge HTML for variable rates"""
        if rate_type == "fixed":
            return '<span style="background: #808080; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">FIXED RATE</span>'
        if risk_score == 0:
            return '<span style="background: #808080; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">NO RISK</span>'
        elif risk_score <= 30:
            return '<span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">LOW RISK</span>'
        elif risk_score <= 60:
            return '<span style="background: #f59e0b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">MODERATE RISK</span>'
        else:
            return '<span style="background: #ef4444; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">HIGH RISK</span>'

    def calculate_scenario(scenario_name, scenario_inputs, current_mortgage):
        def get_input_value(input_name: str):
            return scenario_inputs.get(input_name).value

        new_rate = get_input_value("rate")
        rate_type = get_input_value("rate_type")
        double_monthly_payment = get_input_value("double_payment")

        display_name = f"{scenario_name}: {rate_type} {new_rate:.2f}%"


        scenario_config = {
            "name": scenario_name,
            "display_name": display_name,
            "new_rate": new_rate / 100,
            "rate_type": rate_type,
            "principal_paydown": get_input_value("paydown"),
            "new_amortization_years": get_input_value("amortization"),
            "double_up_monthly_payments": get_input_value("double_payment"),
            "extra_annual_payment": get_input_value("annual_payment"),
        }
        planner = MortgageRenewalPlanner(current_mortgage)
        planner.scenario_analysis([scenario_config], MAX_PAYDOWN_AVAILABLE)


        if double_monthly_payment and len(planner.renewal_scenarios) > 0:
            base_payment = planner.renewal_scenarios.get(scenario_name).new_monthly_payment
            planner.renewal_scenarios.get(scenario_name).extra_monthly_payment = base_payment
            planner.renewal_scenarios.get(scenario_name).simulate_new_mortgage()

        planner.calculate_break_even_rates()

        return planner.to_frame().iloc[0] if len(planner.to_frame()) > 0 else None
    return calculate_scenario, format_currency, get_risk_badge, ui_configs


@app.cell
def card_components_generators(DEFAULT_SCENARIO_CONFIGS, mo, ui_configs):
    def card_ui_inputs_generator(
        configs_dict=DEFAULT_SCENARIO_CONFIGS, 
        ui_configs=ui_configs
    ):
        card_inputs_data = {}
        for s, v in configs_dict.items():
            card_inputs_data[s] = mo.ui.dictionary({
                "rate": mo.ui.number(
                    label=ui_configs["rate_input"]["label"],
                    value=v.get("new_rate", ui_configs["rate_input"]["value"]),
                    start=ui_configs["rate_input"]["start"],
                    stop=ui_configs["rate_input"]["stop"],
                    step=ui_configs["rate_input"]["step"],
                    full_width=False,
                ),
                "rate_type": mo.ui.radio(
                    options=ui_configs["rate_type_input"]["options"],
                    value=v.get("rate_type", ui_configs["rate_type_input"]["value"]),
                    label=ui_configs["rate_type_input"]["label"],
                    inline=True,
                ),
                "paydown": mo.ui.number(
                    start=ui_configs["paydown_input"]["start"],
                    stop=ui_configs["paydown_input"]["stop"],
                    step=ui_configs["paydown_input"]["step"],
                    value=v.get("principal_paydown", ui_configs["paydown_input"]["value"]),
                    label=ui_configs["paydown_input"]["label"],
                ),
                "amortization": mo.ui.dropdown(
                    options=ui_configs["amortization_input"]["options"],
                    value=v.get("new_amortization_years", ui_configs["amortization_input"]["value"]),
                    label=ui_configs["amortization_input"]["label"],
                ),
                "double_payment": mo.ui.checkbox(
                    label=ui_configs["double_payment_input"]["label"],
                    value=v.get("double_up_monthly_payments", ui_configs["double_payment_input"]["value"]),
                ),
                "annual_payment": mo.ui.number(
                    label=ui_configs["annual_payment_input"]["label"],
                    value=v.get("extra_annual_payment", ui_configs["annual_payment_input"]["value"]),
                    start=ui_configs["annual_payment_input"]["start"],
                    stop=ui_configs["annual_payment_input"]["stop"],
                    step=ui_configs["annual_payment_input"]["step"],
                ),
            })
        return mo.ui.dictionary(card_inputs_data)
    return (card_ui_inputs_generator,)


@app.cell
def scenario_card_inputs(card_ui_inputs_generator):
    card_inputs = card_ui_inputs_generator()
    return (card_inputs,)


@app.cell
def scenario_calculations(calculate_scenario, card_inputs, current_mortgage):
    _trigger = card_inputs.values()
    # Now calculate scenarios - marimo will re-run this when any UI changes
    scenario_results = {}
    for _k, v in card_inputs.items():
        scenario_results[_k] = calculate_scenario(_k, v, current_mortgage)
    return (scenario_results,)


@app.cell
def create_interactive_scenario_card(
    balance_at_renewal,
    format_currency,
    get_risk_badge,
    mo,
):
    """Create an interactive scenario card with form inputs and results"""

    def interactive_card(
        scenario_num,
        inputs,
        result_row,
    ):
        """
        Generate an interactive scenario card

        Args:
            scenario_num: Scenario number
            inputs: Scenario inputs (dict)
            result_row: Calculated scenario result (pandas Series)
        """

        rate_input = inputs.get("rate")
        rate_type_input = inputs.get("rate_type")
        paydown_input = inputs.get("paydown")
        amortization_input = inputs.get("amortization")
        double_payment_input = inputs.get("double_payment")
        annual_payment_input = inputs.get("annual_payment")

        if result_row is None:
            return mo.md("_Error calculating scenario_")

        is_variable = result_row.get('rate_type', 'fixed') == 'variable'

        # Card styling
        border_color = "#6b7280" if is_variable else "#3b82f6"
        border_style = f"2px dashed {border_color}" if is_variable else f"2px solid {border_color}"

        # Risk badge
        risk_badge = ""
        if is_variable:
            risk_badge = get_risk_badge(result_row.get('risk_score', 0))
        else:
            risk_badge = get_risk_badge(0, rate_type="fixed")

        # Monthly payment (base + extra monthly)
        base_monthly_payment = result_row['new_monthly_payment']
        monthly_display = format_currency(base_monthly_payment)
        annual_payment = result_row.get('new_extra_annual_payment', 0)

        # Show breakdown if there's an extra payment
        payment_breakdown = ""
        if double_payment_input.value:
            payment_breakdown = f"(2x {format_currency(base_monthly_payment/2)})"
        
        # Annual payment
        if annual_payment > 0:
            annual_payment_display = f"Extra Annual Payment: {format_currency(annual_payment)}"
        else:
            annual_payment_display = "No Extra Annual Payments"

        # Variable rate range
        payment_range_display = ""
        if is_variable and result_row.get('payment_range_min', 0) > 0:
            payment_range_display = f"Range: {format_currency(result_row['payment_range_min'])} - {format_currency(result_row['payment_range_max'])}"

        # After 5 years
        remaining = result_row['total_remaining']
        interest = result_row['total_term_interest']
        new_principal = result_row['new_principal']

        # Interest range for variable
        interest_range_display = ""
        if is_variable and result_row.get('interest_range_min', 0) > 0:
            interest_range_display = f" ({format_currency(result_row['interest_range_min'])} - {format_currency(result_row['interest_range_max'])})"

        # Break-even info for variable
        breakeven_display = ""
        if is_variable and result_row.get('break_even_rate', 0) > 0:
            breakeven_display = f"Break-even: {result_row['break_even_rate']*100:.2f}% | Sensitivity: +0.25% = +${result_row.get('rate_sensitivity', 0):.0f}/mo"

        # Assemble the card
        card_content = mo.vstack([
            # Header
            mo.md(f"### Scenario {scenario_num}"),
            mo.Html(risk_badge) if risk_badge else mo.md(""),

            mo.md("---"),

            # Input form
            mo.md("**Customize This Scenario:**"),
            rate_type_input,
            rate_input,
            paydown_input,
            mo.md(f"**New Principal:** {format_currency(new_principal)}"),
            amortization_input,
            double_payment_input,
            annual_payment_input,
            mo.md("---"),

            # Results
            mo.md("**Monthly Payment**"),
            mo.md(f"## {monthly_display}"),
            mo.md(f"_{payment_breakdown}_") if payment_breakdown else mo.md(" "),
            mo.md(f"_{annual_payment_display}_") if annual_payment_display else mo.md(" "),
            mo.md(f"_{payment_range_display}_") if payment_range_display else mo.md(" "),
            mo.md(f"Payoff Time: **{result_row['payoff_time_months']} months**"),

            mo.md("---"),
            mo.md("**After 5 Years:**"),
            mo.md(f"Remaining: **{format_currency(remaining)}**"),
            mo.md(f"Interest paid: **{format_currency(interest)}**"),
            mo.md(f"_Interest range: {interest_range_display}_") if interest_range_display else mo.md(" \n"),

            mo.md(f"_ℹ️ {breakeven_display}_") if breakeven_display else mo.md(" "),
        ])

        # Wrap in styled container
        card_html = f"""
        <div style="border: {border_style}; border-radius: 6px; padding: 6px; background: white; min-width: 220px; max-width: 300px;">
        """

        return mo.vstack([
            mo.Html(card_html),
            card_content,
            mo.Html("</div>")
        ])
    return (interactive_card,)


@app.cell
def render_scenario_cards(card_inputs, interactive_card, mo, scenario_results):

    cards = []
    for _i, (k, values) in enumerate(card_inputs.items()):
        card_i = interactive_card(_i+1, values, scenario_results.get(k))
        cards.append(card_i)

    # Display cards in rows
    scenarios_display = mo.vstack([
        mo.md("## Compare Renewal Scenarios"),
        mo.md("_Edit any parameter in a card to see instant updates_"),
        mo.md("---"),
        mo.hstack([cards[0], cards[1], cards[2], cards[3], cards[4]], justify="start", gap=1, wrap=True),
    ])
    return (scenarios_display,)


@app.cell
def summary_comparison(
    balance_at_renewal,
    format_currency,
    mo,
    pd,
    remaining_amortization,
    scenario_results,
):
    """Create a summary comparison table"""

    # Filter out None results
    valid_results = [{**r, "name": n} for n, r in scenario_results.items() if r is not None]

    if not valid_results:
        summary_table_display = mo.md("_No valid scenarios to compare_")
    else:
        summary_data = []
        for i, result in enumerate(valid_results, 1):
            # Calculate total monthly payment (base + extra)
            total_monthly = result['new_monthly_payment'] + result.get('extra_monthly_payment', 0)

            summary_data.append({
                'Scenario': f"Scenario {i}",
                'Rate': f"{result.get('rate_type', 'fixed').title()} {result['new_rate']*100:.2f}%",
                'Paydown': format_currency(result['paydown_amount']),
                'Monthly Payment': format_currency(total_monthly),
                'Total Interest (5yr)': format_currency(result['total_term_interest']),
                'Remaining Balance': format_currency(result['total_remaining']),
            })

        summary_df = pd.DataFrame(summary_data)

        summary_table_display = mo.vstack([
            mo.md("## Summary Comparison"),
            mo.md(f"**Balance at renewal:** {format_currency(balance_at_renewal)} | **Remaining amortization:** {remaining_amortization} months"),
            mo.md("---"),
            mo.ui.table(summary_df, selection=None),
            mo.md("---"),
            mo.md("### Quick Tips"),
            mo.md("- **Lowest monthly payment** = Better cash flow"),
            mo.md("- **Lowest total interest** = Less cost over time"),
            mo.md("- **Variable rates** = More risk but potential savings"),
            mo.md("- **Higher paydown** = Lower interest and faster payoff"),
        ])
    return (summary_table_display,)


@app.cell
def final_layout(
    current_mortgage_display,
    mo,
    orig_form,
    scenarios_display,
    summary_table_display,
):
    """Final layout"""
    main_content = mo.vstack([
    mo.md("# 🏠 Canadian Mortgage Renewal Calculator"),
    mo.md("_Interactive scenario comparison tool - edit any card to see instant results_"),
            mo.md("---"),
    orig_form,
            mo.md("---"),
    current_mortgage_display,
    scenarios_display,
    mo.md("---"),
    summary_table_display,
    ])
    return (main_content,)


@app.cell
def _(main_content):
    main_content
    return


if __name__ == "__main__":
    app.run()
