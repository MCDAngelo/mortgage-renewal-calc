"""
Integration tests for end-to-end mortgage calculation workflows.

Tests complete workflows from mortgage creation through renewal planning,
including real-world scenarios.
"""

import pytest
from datetime import datetime
from canadian_mortgage_calculator import CanadianMortgageCalculator
from mortgage_renewal import MortgageRenewalPlanner


@pytest.mark.integration
class TestRealWorldMortgages:
    """Test with realistic mortgage scenarios and parameters."""
    
    def test_typical_canadian_mortgage(self):
        """Test calculation with typical Canadian mortgage parameters."""
        mortgage = CanadianMortgageCalculator(
            original_principal=500000,
            annual_rate=0.0549,  # 5.49% typical rate
            amortization_months=300,  # 25 years
            term_months=60,  # 5 year term
            start_date=datetime(2024, 1, 1),
            verbose=False
        )
        
        schedule = mortgage.create_full_amortization_schedule()
        
        # Sanity checks
        assert mortgage.monthly_payment > 2500  # Reasonable payment
        assert mortgage.monthly_payment < 4000
        assert len(schedule) == 300  # Full amortization schedule
        assert mortgage.balance_at_renewal < 500000
        assert mortgage.balance_at_renewal > 400000  # After 5 years
    
    def test_high_ratio_mortgage(self):
        """Test high-ratio mortgage (>80% LTV) scenario."""
        mortgage = CanadianMortgageCalculator(
            original_principal=450000,  # 90% of 500k home
            annual_rate=0.0599,
            amortization_months=300,
            term_months=60,
            start_date=datetime(2024, 1, 1),
            verbose=False
        )
        
        schedule = mortgage.create_full_amortization_schedule()
        mortgage.print_mortgage_summary(schedule)
        
        assert mortgage.monthly_payment > 0
        assert len(schedule) > 0
        assert mortgage.balance_at_renewal < 450000
    
    @pytest.mark.slow
    def test_accelerated_payoff_scenario(self):
        """Test mortgage with aggressive extra payments."""
        mortgage = CanadianMortgageCalculator(
            original_principal=400000,
            annual_rate=0.05,
            amortization_months=300,
            term_months=60,
            start_date=datetime(2024, 1, 1),
            verbose=False
        )
        
        # Make 10% annual extra payments
        extra_annual = 40000
        schedule = mortgage.create_full_amortization_schedule(extra_annual_payment=extra_annual)
        
        # Should pay off much faster
        payoff_months = len(schedule)
        assert payoff_months < 150  # Should be well under 25 years


@pytest.mark.integration
class TestCompleteRenewalWorkflow:
    """Test complete mortgage renewal workflow from start to finish."""
    
    def test_end_to_end_renewal_planning(self):
        """Test complete workflow: create mortgage, calculate schedule, plan renewal."""
        # Step 1: Create original mortgage
        original_mortgage = CanadianMortgageCalculator(
            original_principal=600000,
            annual_rate=0.0199,
            amortization_months=300,
            term_months=60,
            start_date=datetime(2020, 1, 1),
            verbose=False
        )
        
        # Step 2: Generate amortization schedule
        original_schedule = original_mortgage.create_full_amortization_schedule()
        assert len(original_schedule) > 0
        assert original_mortgage.balance_at_renewal > 0
        
        # Step 3: Create renewal planner
        planner = MortgageRenewalPlanner(original_mortgage)
        
        # Step 4: Define multiple renewal scenarios
        scenarios = [
            {
                'name': 'Conservative - no paydown',
                'new_rate': 0.045,
                'principal_paydown': 0,
                'extra_monthly_payment': 0,
                'extra_annual_payment': 0,
            },
            {
                'name': 'Moderate - $50k paydown',
                'new_rate': 0.045,
                'principal_paydown': 50000,
                'extra_monthly_payment': 0,
                'extra_annual_payment': 0,
            },
            {
                'name': 'Aggressive - $100k down + extras',
                'new_rate': 0.045,
                'principal_paydown': 100000,
                'extra_monthly_payment': 500,
                'extra_annual_payment': 30000,
            },
        ]
        
        # Step 5: Analyze scenarios
        planner.scenario_analysis(scenarios, max_paydown=150000)
        results = planner.to_frame()
        
        # Step 6: Verify results
        assert len(results) == 3
        assert all(results['new_monthly_payment'] > 0)
        assert all(results['total_term_interest'] > 0)
        
        # Conservative should have highest balance remaining
        conservative = results[results['scenario_name'] == 'Conservative - no paydown']
        aggressive = results[results['scenario_name'] == 'Aggressive - $100k down + extras']
        
        assert conservative['new_principal'].iloc[0] > aggressive['new_principal'].iloc[0]
    
    def test_comparing_interest_rate_scenarios(self):
        """Test comparing different interest rate scenarios at renewal."""
        # Current mortgage at low rate
        current_mortgage = CanadianMortgageCalculator(
            original_principal=500000,
            annual_rate=0.0199,  # Old low rate
            amortization_months=300,
            term_months=60,
            start_date=datetime(2019, 1, 1),
            verbose=False
        )
        current_mortgage.create_full_amortization_schedule()
        
        # Plan for various rate environments
        planner = MortgageRenewalPlanner(current_mortgage)
        rate_scenarios = [
            {'name': 'Best case - 3.5%', 'new_rate': 0.035, 'principal_paydown': 0},
            {'name': 'Likely - 4.5%', 'new_rate': 0.045, 'principal_paydown': 0},
            {'name': 'Worst case - 5.5%', 'new_rate': 0.055, 'principal_paydown': 0},
        ]
        
        planner.scenario_analysis(rate_scenarios, max_paydown=100000)
        results = planner.to_frame()
        
        # Verify rate impacts
        best_case = results[results['scenario_name'] == 'Best case - 3.5%']
        worst_case = results[results['scenario_name'] == 'Worst case - 5.5%']
        
        # Higher rate should mean higher payment and more interest
        assert worst_case['new_monthly_payment'].iloc[0] > best_case['new_monthly_payment'].iloc[0]
        assert worst_case['total_term_interest'].iloc[0] > best_case['total_term_interest'].iloc[0]
    
    @pytest.mark.slow
    def test_paydown_vs_investment_tradeoff(self):
        """Test the analysis of paying down mortgage vs investing."""
        current_mortgage = CanadianMortgageCalculator(
            original_principal=700000,
            annual_rate=0.0249,
            amortization_months=360,
            term_months=60,
            start_date=datetime(2019, 6, 1),
            verbose=False
        )
        current_mortgage.create_full_amortization_schedule()
        
        available_cash = 200000
        planner = MortgageRenewalPlanner(current_mortgage)
        
        # Scenario 1: Pay down maximum
        # Scenario 2: Pay down minimum, invest rest
        scenarios = [
            {
                'name': 'Max paydown',
                'new_rate': 0.04,
                'principal_paydown': 200000,
                'extra_monthly_payment': 0,
                'extra_annual_payment': 0,
            },
            {
                'name': 'Min paydown',
                'new_rate': 0.04,
                'principal_paydown': 0,
                'extra_monthly_payment': 0,
                'extra_annual_payment': 0,
            },
        ]
        
        planner.scenario_analysis(scenarios, max_paydown=available_cash)
        results = planner.to_frame()
        
        # Verify investment scenarios are calculated
        assert 'Max paydown' in planner.renewal_scenarios
        assert 'Min paydown' in planner.renewal_scenarios
        
        # Check that investment returns are calculated for min paydown
        if 'Min paydown' in planner.investment_return_scenarios:
            investment_returns = planner.investment_return_scenarios['Min paydown']
            assert len(investment_returns) > 0  # Should have multiple rate scenarios

