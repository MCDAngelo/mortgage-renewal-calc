"""
Tests for MortgageRenewalPlanner class.

Tests renewal scenario planning including:
- Single and multiple scenario analysis
- Principal paydown options
- Rate comparisons
- Results dataframe structure
"""

from datetime import datetime
from canadian_mortgage_calculator import CanadianMortgageCalculator
from mortgage_renewal import MortgageRenewalPlanner


class TestMortgageRenewalScenarios:
    """Test mortgage renewal scenario planning features."""
    
    def test_single_renewal_scenario(self, renewal_planner):
        """Test basic renewal scenario analysis."""
        scenarios = [
            {
                'name': '3.75% rate',
                'new_rate': 0.0375,
                'principal_paydown': 0,
                'extra_monthly_payment': 0,
                'extra_annual_payment': 0,
            }
        ]
        
        renewal_planner.scenario_analysis(scenarios, max_paydown=300000)
        results_df = renewal_planner.to_frame()
        
        assert len(results_df) == 1
        assert results_df.iloc[0]['scenario_name'] == '3.75% rate'
        assert results_df.iloc[0]['new_rate'] == 0.0375
    
    def test_renewal_with_principal_paydown(self, large_mortgage):
        """Test renewal scenario with principal paydown."""
        large_mortgage.create_full_amortization_schedule()
        planner = MortgageRenewalPlanner(large_mortgage)
        
        scenarios = [
            {
                'name': '3.75% + $150k down',
                'new_rate': 0.0375,
                'principal_paydown': 150000,
                'extra_monthly_payment': 0,
                'extra_annual_payment': 0,
            }
        ]
        
        planner.scenario_analysis(scenarios, max_paydown=300000)
        results_df = planner.to_frame()
        
        # New principal should be reduced by paydown amount
        expected_new_principal = large_mortgage.balance_at_renewal - 150000
        assert abs(results_df.iloc[0]['new_principal'] - expected_new_principal) < 0.01
        assert results_df.iloc[0]['paydown_amount'] == 150000
    
    def test_multiple_renewal_scenarios(self, sample_renewal_scenarios):
        """Test analysis of multiple renewal scenarios."""
        current_mortgage = CanadianMortgageCalculator(
            original_principal=500000,
            annual_rate=0.02,
            amortization_months=300,
            term_months=60,
            start_date=datetime(2020, 1, 1),
            verbose=False
        )
        current_mortgage.create_full_amortization_schedule()
        
        planner = MortgageRenewalPlanner(current_mortgage)
        planner.scenario_analysis(sample_renewal_scenarios, max_paydown=200000)
        results_df = planner.to_frame()
        
        assert len(results_df) == 3
        
        # Higher rates should result in higher interest costs
        low_interest = results_df[results_df['scenario_name'] == 'Low rate - no paydown']['total_term_interest'].iloc[0]
        high_interest = results_df[results_df['scenario_name'] == 'High rate - aggressive paydown']['total_term_interest'].iloc[0]
        
        # Note: high_interest might be lower despite higher rate due to aggressive paydown
        # Just verify both are calculated
        assert low_interest > 0
        assert high_interest > 0
    
    def test_renewal_results_dataframe_structure(self, renewal_planner):
        """Test that renewal results have all expected columns."""
        scenarios = [
            {'name': 'Test scenario', 'new_rate': 0.04, 'principal_paydown': 50000}
        ]
        
        renewal_planner.scenario_analysis(scenarios, max_paydown=100000)
        results_df = renewal_planner.to_frame()
        
        expected_columns = [
            'scenario_name', 'paydown_amount', 'new_rate', 'new_principal',
            'new_term_amortization', 'new_monthly_payment', 'total_term_interest'
        ]
        
        for col in expected_columns:
            assert col in results_df.columns, f"Missing column: {col}"
    
    def test_paydown_reduces_interest_cost(self, renewal_planner):
        """Test that principal paydown reduces total interest cost."""
        scenarios = [
            {'name': 'No paydown', 'new_rate': 0.04, 'principal_paydown': 0},
            {'name': '$100k paydown', 'new_rate': 0.04, 'principal_paydown': 100000},
        ]
        
        renewal_planner.scenario_analysis(scenarios, max_paydown=200000)
        results_df = renewal_planner.to_frame()
        
        no_paydown_interest = results_df[results_df['scenario_name'] == 'No paydown']['total_term_interest'].iloc[0]
        paydown_interest = results_df[results_df['scenario_name'] == '$100k paydown']['total_term_interest'].iloc[0]
        
        # Paydown should reduce interest cost
        assert paydown_interest < no_paydown_interest
    
    def test_higher_rate_increases_payment(self, renewal_planner):
        """Test that higher interest rate increases monthly payment."""
        scenarios = [
            {'name': 'Low rate', 'new_rate': 0.03, 'principal_paydown': 0},
            {'name': 'High rate', 'new_rate': 0.06, 'principal_paydown': 0},
        ]
        
        renewal_planner.scenario_analysis(scenarios, max_paydown=100000)
        results_df = renewal_planner.to_frame()
        
        low_rate_payment = results_df[results_df['scenario_name'] == 'Low rate']['new_monthly_payment'].iloc[0]
        high_rate_payment = results_df[results_df['scenario_name'] == 'High rate']['new_monthly_payment'].iloc[0]
        
        assert high_rate_payment > low_rate_payment


class TestRenewalScenarioEdgeCases:
    """Test edge cases in renewal scenario planning."""
    
    def test_full_payoff_at_renewal(self, large_mortgage):
        """Test scenario where mortgage is fully paid off at renewal."""
        large_mortgage.create_full_amortization_schedule()
        planner = MortgageRenewalPlanner(large_mortgage)
        
        # Pay off entire remaining balance
        full_balance = large_mortgage.balance_at_renewal
        scenarios = [
            {
                'name': 'Full payoff',
                'new_rate': 0.04,
                'principal_paydown': full_balance,
                'extra_monthly_payment': 0,
                'extra_annual_payment': 0,
            }
        ]
        
        planner.scenario_analysis(scenarios, max_paydown=full_balance)
        results_df = planner.to_frame()
        
        # New principal should be zero (or very close)
        assert abs(results_df.iloc[0]['new_principal']) < 1
    
    def test_zero_rate_renewal(self, typical_mortgage):
        """Test renewal with zero interest rate."""
        typical_mortgage.create_full_amortization_schedule()
        planner = MortgageRenewalPlanner(typical_mortgage)
        
        scenarios = [
            {'name': 'Zero rate', 'new_rate': 0.0, 'principal_paydown': 0}
        ]
        
        planner.scenario_analysis(scenarios, max_paydown=100000)
        results_df = planner.to_frame()
        
        # Should still work, interest should be zero
        assert results_df.iloc[0]['total_term_interest'] == 0

