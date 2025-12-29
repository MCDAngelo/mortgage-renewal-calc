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
                - 'rate_type': 'fixed' or 'variable' (default: 'fixed')
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
    
    def calculate_break_even_rates(self):
        """
        Calculate break-even rates between fixed and variable scenarios.
        For each variable scenario, find the equivalent fixed rate where costs are equal.
        """
        fixed_scenarios = {name: sc for name, sc in self.renewal_scenarios.items() if sc.rate_type == 'fixed'}
        variable_scenarios = {name: sc for name, sc in self.renewal_scenarios.items() if sc.rate_type == 'variable'}
        
        for var_name, var_sc in variable_scenarios.items():
            # Find closest fixed scenario with same paydown and extra payments
            closest_fixed = None
            min_diff = float('inf')
            
            for fix_name, fix_sc in fixed_scenarios.items():
                if (fix_sc.principal_paydown == var_sc.principal_paydown and
                    fix_sc.extra_monthly_payment == var_sc.extra_monthly_payment and
                    fix_sc.extra_annual_payment == var_sc.extra_annual_payment):
                    
                    rate_diff = abs(fix_sc.new_rate - var_sc.new_rate)
                    if rate_diff < min_diff:
                        min_diff = rate_diff
                        closest_fixed = fix_sc
            
            if closest_fixed and var_sc.new_mortgage:
                # Calculate break-even: at what rate does variable equal fixed interest?
                # Simple approximation: if fixed interest > variable expected, break-even is above variable rate
                if closest_fixed.total_term_interest > var_sc.total_term_interest:
                    # Variable is better, break-even is somewhere above variable rate
                    interest_diff = closest_fixed.total_term_interest - var_sc.total_term_interest
                    # Rough estimate: each 0.25% rate change affects interest by rate_sensitivity * 60 months
                    if var_sc.rate_sensitivity > 0:
                        rate_increase_needed = interest_diff / (var_sc.rate_sensitivity * 60)
                        var_sc.break_even_rate = var_sc.new_rate + (rate_increase_needed * 0.0025)
                    else:
                        var_sc.break_even_rate = closest_fixed.new_rate
                else:
                    # Fixed is better, variable would need to drop
                    var_sc.break_even_rate = var_sc.new_rate - 0.005

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