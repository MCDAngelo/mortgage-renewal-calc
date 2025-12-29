from dataclasses import dataclass
from canadian_mortgage_calculator import CanadianMortgageCalculator
import logging
import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

@dataclass
class RenewalScenarioResult:
    scenario_name: str
    paydown_amount: float
    new_rate: float
    rate_type: str  # 'fixed' or 'variable'
    new_principal: float
    new_term_amortization: int
    new_monthly_payment: float
    double_up_monthly_payments: bool
    new_extra_annual_payment: float
    payoff_time_months: int
    total_term_interest: float
    total_term_cost: float
    total_remaining: float
    payoff_time_months: int
    # Variable rate specific fields
    payment_range_min: float = 0  # Best case for variable
    payment_range_max: float = 0  # Worst case for variable
    interest_range_min: float = 0  # Best case total interest
    interest_range_max: float = 0  # Worst case total interest
    risk_score: int = 0  # 0-100, only for variable rates
    break_even_rate: float = 0  # Rate at which variable equals fixed
    rate_sensitivity: float = 0  # $ change per 0.25% rate change

    def to_frame(self):
        return pd.DataFrame([self.__dict__])

class RenewalScenario:
    """
    A class to represent the results of a renewal scenario.
    """
    def __init__(self, scenario_config: dict, current_mortgage: CanadianMortgageCalculator):
        self.scenario_name = scenario_config.get('name', 'Unknown')
        self.new_rate = scenario_config.get('new_rate', None)
        if self.new_rate is None:
            raise ValueError("new_rate is required")
        self.rate_type = scenario_config.get('rate_type', 'fixed')  # 'fixed' or 'variable'
        self.current_mortgage = current_mortgage
        self.new_term = scenario_config.get('new_term', 5)
        self.principal_paydown = scenario_config.get('principal_paydown', 0)
        self.extra_annual_payment = scenario_config.get('extra_annual_payment', 0)
        self.double_up_monthly_payments = scenario_config.get('double_up_monthly_payments', False)
        self.new_principal = (
            self.current_mortgage.balance_at_renewal - self.principal_paydown
        )
        self.new_term_amortization_years = scenario_config.get('new_amortization_years', None)
        self.new_term_amortization = self.new_term_amortization_years * 12 if self.new_term_amortization_years is not None else None
        self.new_mortgage = None
        self.new_mortgage_schedule = None
        self.new_monthly_payment = None
        self.total_term_interest = None
        self.total_term_cost = None
        self.total_remaining = None
        self.payoff_time_months = None
        # Variable rate fields
        self.payment_range_min = 0
        self.payment_range_max = 0
        self.interest_range_min = 0
        self.interest_range_max = 0
        self.risk_score = 0
        self.break_even_rate = 0
        self.rate_sensitivity = 0

    def combine_results(self):
        """
        Combine the results of the renewal scenario.
        """      
        self.results = RenewalScenarioResult(
            scenario_name=self.scenario_name,
            paydown_amount=self.principal_paydown,
            double_up_monthly_payments=self.double_up_monthly_payments,
            new_rate=self.new_rate,
            rate_type=self.rate_type,
            new_principal=round(self.new_principal, 2),
            new_term_amortization= 0 if self.new_term_amortization is None else self.new_term_amortization,
            new_monthly_payment= 0 if self.new_monthly_payment is None else round(self.new_monthly_payment, 2),
            new_extra_annual_payment= 0 if self.extra_annual_payment is None else self.extra_annual_payment,
            payoff_time_months= 0 if self.payoff_time_months is None else self.payoff_time_months,
            total_term_interest= 0 if self.total_term_interest is None else round(self.total_term_interest, 2),
            total_term_cost= 0 if self.total_term_cost is None else round(self.total_term_cost, 2),
            total_remaining= 0 if self.total_remaining is None else round(self.total_remaining, 2),
            payment_range_min=round(self.payment_range_min, 2),
            payment_range_max=round(self.payment_range_max, 2),
            interest_range_min=round(self.interest_range_min, 2),
            interest_range_max=round(self.interest_range_max, 2),
            risk_score=self.risk_score,
            break_even_rate=round(self.break_even_rate, 4),
            rate_sensitivity=round(self.rate_sensitivity, 2),
        )
    
    def to_frame(self):
        return self.results.to_frame()

    def find_best_standard_amortization(self):
        """
        Find the best standard Canadian amortization period for a target payment.
        Canadian mortgages typically offer: 5, 10, 15, 20, 25, 30 year amortizations.
        This function tests each standard option and finds the closest match.
        """
        base_case = CanadianMortgageCalculator(
            self.new_principal, 
            self.new_rate, 
            self.current_mortgage.amortization_months
        )
        def calculate_payment(years):
            months = years * 12
            return base_case.calculate_payment(amortization_months=months)

        def calculate_difference(years):
            calculated_payment = calculate_payment(years)
            difference = calculated_payment - self.current_mortgage.monthly_payment
            return difference

        self.finding_best_amortization_results = [
            {
                'years': y,
                'months': y * 12,
                'payment': calculate_payment(y),
                'difference': calculate_difference(y),
            } for y in [5, 10, 15, 20, 25, 30]
        ]

        self.best_option = min(self.finding_best_amortization_results, key=lambda x: abs(x['difference']))
        self.new_term_amortization = self.best_option['months']

    def simulate_new_mortgage(self):
        """
        Simulate the new mortgage for the renewal scenario.
        """
        # If mortgage is fully paid off, no need to simulate
        if self.new_principal <= 0:
            self.total_term_interest = 0
            self.total_term_cost = 0
            self.total_remaining = 0
            self.combine_results()
            return
            
        self.new_mortgage = CanadianMortgageCalculator(self.new_principal, self.new_rate, self.new_term_amortization, double_up_monthly_payments=self.double_up_monthly_payments)
        self.new_mortgage_schedule = (
            self.new_mortgage.create_full_amortization_schedule(extra_annual_payment=self.extra_annual_payment)
        )
        self.new_monthly_payment = self.new_mortgage.monthly_payment
        
        # Handle case where schedule might be empty or shorter than term
        if len(self.new_mortgage_schedule) == 0:
            self.total_term_interest = 0
            self.total_term_cost = 0
            self.total_remaining = 0
            self.payoff_time_months = 0
        else:
            end_of_term_idx = min(self.new_term*12, len(self.new_mortgage_schedule)-1)
            end_of_term = self.new_mortgage_schedule.iloc[end_of_term_idx]
            self.total_term_interest = end_of_term['Cumulative_Interest']
            self.total_term_cost = end_of_term['Cumulative_Principal']
            self.total_remaining = self.new_mortgage.balance_at_renewal
            self.payoff_time_months = self.new_mortgage.payoff_time_months
        
        # Calculate variable rate scenarios if rate_type is 'variable'
        if self.rate_type == 'variable':
            self.calculate_variable_rate_risk(double_up_monthly_payments=self.double_up_monthly_payments)
        
        self.combine_results()

    def calculate_variable_rate_risk(self, double_up_monthly_payments: bool):
        """
        Calculate risk metrics for variable rate scenarios.
        Simulates best case, expected case, and worst case rate changes.
        """
        if self.new_principal <= 0:
            return
        
        # Rate change scenarios (in decimal, e.g., 0.01 = 1%)
        rate_changes = {
            'best': -0.01,      # Rates drop 1%
            'expected': 0.0,    # Rates stay same (already calculated)
            'worst': 0.02,      # Rates rise 2%
        }
        
        scenarios = {}
        for scenario_name, rate_change in rate_changes.items():
            adjusted_rate = self.new_rate + rate_change
            adjusted_mortgage = CanadianMortgageCalculator(
                self.new_principal, 
                adjusted_rate, 
                self.new_term_amortization,
                double_up_monthly_payments=double_up_monthly_payments
            )
            adjusted_schedule = adjusted_mortgage.create_full_amortization_schedule(
                extra_annual_payment=self.extra_annual_payment
            )
            
            if len(adjusted_schedule) > 0:
                end_of_term_idx = min(self.new_term*12, len(adjusted_schedule)-1)
                end_of_term = adjusted_schedule.iloc[end_of_term_idx]
                scenarios[scenario_name] = {
                    'payment': adjusted_mortgage.monthly_payment,
                    'interest': end_of_term['Cumulative_Interest']
                }
            else:
                scenarios[scenario_name] = {
                    'payment': 0,
                    'interest': 0
                }
        
        # Set payment and interest ranges
        self.payment_range_min = scenarios['best']['payment']
        self.payment_range_max = scenarios['worst']['payment']
        self.interest_range_min = scenarios['best']['interest']
        self.interest_range_max = scenarios['worst']['interest']
        
        # Calculate rate sensitivity (change per 0.25% increase)
        if self.new_mortgage and self.new_mortgage.monthly_payment:
            rate_quarter_percent = self.new_rate + 0.0025
            temp_mortgage = CanadianMortgageCalculator(
                self.new_principal,
                rate_quarter_percent,
                self.new_term_amortization,
                double_up_monthly_payments=double_up_monthly_payments
            )
            self.rate_sensitivity = temp_mortgage.monthly_payment - self.new_mortgage.monthly_payment
        
        # Calculate risk score (0-100)
        # Based on payment volatility and rate increase potential
        payment_range = self.payment_range_max - self.payment_range_min
        if self.new_mortgage and self.new_mortgage.monthly_payment > 0:
            payment_volatility_pct = (payment_range / self.new_mortgage.monthly_payment) * 100
            # Risk score: higher volatility = higher risk
            # 0-15% volatility = Low (0-30)
            # 15-30% volatility = Moderate (31-60)
            # 30%+ volatility = High (61-100)
            self.risk_score = min(100, int(payment_volatility_pct * 2))
        else:
            self.risk_score = 50  # Default moderate risk
        
        # Break-even rate calculation (placeholder - would compare to a fixed rate scenario)
        # This will be calculated more accurately when we have a fixed rate to compare to
        self.break_even_rate = self.new_rate + 0.005  # Rough estimate: 0.5% above current