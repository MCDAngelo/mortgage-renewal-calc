import pandas as pd
from canadian_mortgage_calculator import CanadianMortgageCalculator
from renewal_scenario import RenewalScenario

class MortgageRenewalPlanner:
    def __init__(self, current_mortgage: CanadianMortgageCalculator):
        """
        Initialize the mortgage renewal planner.
        
        Args:
            CanadianMortgageCalculator: CanadianMortgageCalculator object
        """
        self.current_mortgage = current_mortgage
        self.current_mortgage_schedule = current_mortgage.create_full_amortization_schedule()
    
    def scenario_analysis(self, scenarios, max_paydown):
        """
        Analyze multiple renewal scenarios.
        
        Args:
            scenarios: List of dictionaries with keys:
                - 'name': Scenario name
                - 'new_rate': New annual interest rate
                - 'new_mortgage_term': New mortgage term in years (default: 5)
                - 'new_term_amortization': New amortization in months (default: None)
                - 'principal_paydown': Amount to pay down at renewal (default: 0)
                - 'extra_monthly_payment': Amount to pay extra each month (default: 0)
                - 'extra_yearly_payment': Amount to pay extra each year - up to 10% of the principal (default: 0)
            max_paydown: Maximum amount able to pay down at renewal
        """
        self.renewal_scenarios = {}
        self.investment_return_scenarios = {}

        for scenario in scenarios:
            sc = RenewalScenario(scenario, self.current_mortgage)
            if sc.new_principal <= 0:
                sc.combine_results()
            if sc.new_term_amortization is None:
                sc.find_best_standard_amortization()
            sc.simulate_new_mortgage()
            # Interest gained if principal is applied to investment
            investment_amount = max_paydown - sc.principal_paydown
            if investment_amount > 0:
                self.investment_return_scenarios[scenario['name']] = {}
                investment_return_rates = [0.03, 0.05, 0.10]
                for rate in investment_return_rates:
                    self.investment_return_scenarios[scenario['name']][rate] = self.calculate_compound_interest(
                        investment_amount,
                        rate, 
                        sc.new_term / 12
                    )

            self.renewal_scenarios[scenario['name']] = sc

    def to_frame(self):
        return pd.concat([sc.to_frame() for sc in self.renewal_scenarios.values()])
            
    @staticmethod
    def calculate_compound_interest(principal, annual_rate, years, monthly_contribution=0, 
                                  compounding_frequency=12):
        """
        Calculate compound interest with optional regular contributions.
        
        Args:
            principal: Initial investment amount
            annual_rate: Annual interest rate (as decimal)
            years: Investment period in years
            monthly_contribution: Regular monthly contribution
            compounding_frequency: How often interest compounds per year (default: 12 -> monthly)
            
        Returns:
            Dictionary with investment details
        """
        months = int(years * 12)
        rate_per_period = annual_rate / compounding_frequency
        periods_per_month = compounding_frequency / 12
        
        if monthly_contribution == 0:
            # Simple compound interest
            final_amount = principal * (1 + rate_per_period)**(compounding_frequency * years)
            total_contributions = principal
        else:
            # Compound interest with regular contributions
            if annual_rate == 0:
                final_amount = principal + (monthly_contribution * months)
                total_contributions = principal + (monthly_contribution * months)
            else:
                # Future value of initial principal
                fv_principal = principal * (1 + rate_per_period)**(compounding_frequency * years)
                
                # Future value of annuity (monthly contributions)
                if periods_per_month == 1:
                    # Monthly compounding matches monthly contributions
                    monthly_rate = annual_rate / 12
                    fv_annuity = monthly_contribution * (((1 + monthly_rate)**months - 1) / monthly_rate)
                else:
                    # Approximate for other compounding frequencies
                    effective_monthly_rate = (1 + rate_per_period)**(periods_per_month) - 1
                    fv_annuity = monthly_contribution * (((1 + effective_monthly_rate)**months - 1) / effective_monthly_rate)
                
                final_amount = fv_principal + fv_annuity
                total_contributions = principal + (monthly_contribution * months)
        
        total_interest = final_amount - total_contributions
        
        return {
            'initial_principal': principal,
            'monthly_contribution': monthly_contribution,
            'total_contributions': total_contributions,
            'final_amount': final_amount,
            'total_interest': total_interest,
            'years': years,
            'annual_rate': annual_rate,
            'effective_return': (final_amount / total_contributions - 1) if total_contributions > 0 else 0
        }