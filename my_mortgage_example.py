"""
Example template for calculating your personal mortgage.

IMPORTANT: 
1. Copy this file to 'my_mortgage.py' (which is in .gitignore)
2. Update with your actual mortgage details
3. Do NOT commit my_mortgage.py to git!

This file shows the structure - keep it as a template.
"""

from datetime import datetime
from canadian_mortgage_calculator import CanadianMortgageCalculator
from mortgage_renewal import MortgageRenewalPlanner


def main():
    """Calculate your personal mortgage and renewal scenarios."""
    
    # ===== REPLACE THESE WITH YOUR ACTUAL VALUES =====
    MY_PRINCIPAL = 500000          # Your mortgage amount
    MY_RATE = 0.0549              # Your annual interest rate (5.49% = 0.0549)
    MY_AMORTIZATION = 300         # Amortization in months (25 years = 300)
    MY_TERM = 60                  # Term in months (5 years = 60)
    MY_START_DATE = datetime(2024, 1, 1)  # Your mortgage start date
    
    # Optional: Mortgage gap if you had a payment pause
    # MY_GAP = (datetime(2023, 5, 1), datetime(2023, 8, 1))
    MY_GAP = (None, None)  # No gap
    
    # ===== CREATE YOUR MORTGAGE =====
    my_mortgage = CanadianMortgageCalculator(
        original_principal=MY_PRINCIPAL,
        annual_rate=MY_RATE,
        amortization_months=MY_AMORTIZATION,
        term_months=MY_TERM,
        start_date=MY_START_DATE,
        mortgage_gap=MY_GAP,
        verbose=True
    )
    
    # Generate schedule
    schedule = my_mortgage.create_full_amortization_schedule()
    
    # Print summary
    print("\n" + "="*80)
    print("YOUR MORTGAGE SUMMARY")
    print("="*80)
    my_mortgage.print_mortgage_summary(schedule)
    
    # ===== PLAN RENEWAL SCENARIOS =====
    print("\n" + "="*80)
    print("RENEWAL SCENARIO ANALYSIS")
    print("="*80)
    
    planner = MortgageRenewalPlanner(my_mortgage)
    
    # Define your renewal scenarios
    scenarios = [
        {
            'name': 'Best case - 3.5% rate',
            'new_rate': 0.035,
            'principal_paydown': 0,
            'extra_monthly_payment': 0,
            'extra_annual_payment': 0,
        },
        {
            'name': 'Likely case - 4.5% rate',
            'new_rate': 0.045,
            'principal_paydown': 0,
            'extra_monthly_payment': 0,
            'extra_annual_payment': 0,
        },
        {
            'name': 'Aggressive - $100k down',
            'new_rate': 0.045,
            'principal_paydown': 100000,
            'extra_monthly_payment': 0,
            'extra_annual_payment': 20000,
        },
    ]
    
    # Analyze scenarios
    planner.scenario_analysis(scenarios, max_paydown=200000)
    
    # Get results
    results = planner.to_frame()
    print("\nRenewal Scenario Results:")
    print(results.to_string(index=False))
    
    # Optionally save to CSV (file pattern is in .gitignore)
    # results.to_csv('my_mortgage_renewal_scenarios.csv', index=False)
    

if __name__ == "__main__":
    main()

