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
        MAX_PAYDOWN_AVAILABLE,
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
    MAX_PAYDOWN_AVAILABLE,
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
    current_mortgage,
    current_schedule,
    current_schedule_table,
    form,
    mo,
    plot_scenarios,
    renewal_scenarios_table,
    scenario_run_button,
    visualize_full_amortization_payments,
    visualize_mortgage_term,
):
    sidebar = mo.sidebar(
        form,
        width="30rem",
    )
    results = mo.vstack([
        mo.md(
            '''
            ##Results
            '''
        ),
        mo.accordion({
            "Original Mortgage": mo.vstack([
                current_schedule_table,
                visualize_full_amortization_payments(current_schedule),
                visualize_mortgage_term(current_mortgage, current_schedule)
            ]),
            "Scenarios": mo.vstack([
                plot_scenarios(),
                renewal_scenarios_table
            ])
            if scenario_run_button.value else ""
        }) if scenario_run_button.value else 
        mo.md (
        "Review the inputs and hit Run to see results"
        )

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
    def generate_current_mortgage():
        return CanadianMortgageCalculator(
            original_principal=orig_principal.value,
            annual_rate=orig_rate.value/100,
            amortization_months=orig_amortization.value*12,
            term_months=orig_term.value*12,
            start_date=orig_start_date.value,
            mortgage_gap=(orig_gap_start_date.value, orig_gap_end_date.value) if gap_check.value else (None, None)
        )

    current_mortgage = None
    current_schedule_table = None

    if scenario_run_button.value:
        current_mortgage = generate_current_mortgage()
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
    def run_scenario_analysis():
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
        # Use max paydown from the list
        max_paydown = max(paydown_list) if paydown_list else 300000
        planner.scenario_analysis(scenarios, max_paydown=max_paydown)
        df = planner.to_frame()
        return df, planner

    renewal_scenarios_df = None
    renewal_scenarios_table = None
    if scenario_run_button.value:
        renewal_scenarios_df, planner = run_scenario_analysis()
        renewal_scenarios_table = mo.ui.table(renewal_scenarios_df)
    return renewal_scenarios_table, run_scenario_analysis


@app.cell
def _(alt, mo, run_scenario_analysis):
    def plot_scenarios():
        df, planner = run_scenario_analysis()
        metrics = ["new_principal", "new_term_amortization", "new_monthly_payment",
                "total_term_interest", "total_term_cost", "total_remaining"]
        charts = []
        for m in metrics:
            sub_df = df.sort_values(by=[m], ascending=True)
            plt = alt.Chart(df).mark_bar().encode(
                x="paydown_amount:N",
                y=f"{m}:Q",
                color="new_rate:N",
                column="new_extra_yearly_payment:N",
                facet="new_extra_monthly_payment:N",
            ).properties(
                title=f"{m}"
            )
            charts.append(mo.ui.altair_chart(plt))
        return mo.vstack(charts)
    return (plot_scenarios,)


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
