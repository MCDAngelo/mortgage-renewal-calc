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
    extra_monthly_payment: float
    new_rate: float
    new_principal: float
    new_term_amortization: int
    new_monthly_payment: float
    new_extra_annual_payment: float
    payoff_time_months: int
    total_term_interest: float
    total_term_cost: float
    total_remaining: float

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
        self.current_mortgage = current_mortgage
        self.new_term = scenario_config.get('new_term', 5)
        self.principal_paydown = scenario_config.get('principal_paydown', 0)
        self.extra_monthly_payment = scenario_config.get('extra_monthly_payment', 0)
        self.extra_annual_payment = scenario_config.get('extra_annual_payment', 0)
        self.new_principal = (
            self.current_mortgage.balance_at_renewal - self.principal_paydown
        )
        self.new_term_amortization = None
        self.new_mortgage = None
        self.new_mortgage_schedule = None
        self.total_term_interest = None
        self.total_term_cost = None
        self.total_remaining = None

    def combine_results(self):
        """
        Combine the results of the renewal scenario.
        """      
        self.results = RenewalScenarioResult(
            scenario_name=self.scenario_name,
            paydown_amount=self.principal_paydown,
            extra_monthly_payment=self.extra_monthly_payment,
            new_rate=self.new_rate,
            new_principal=round(self.new_principal, 2),
            new_term_amortization= 0 if self.new_term_amortization is None else self.new_term_amortization,
            new_monthly_payment= 0 if self.new_mortgage is None or self.new_mortgage.monthly_payment is None else self.new_mortgage.monthly_payment,
            new_extra_annual_payment= 0 if self.extra_annual_payment is None else self.extra_annual_payment,
            payoff_time_months= 0 if self.new_mortgage is None or self.new_mortgage.payoff_time_months is None else self.new_mortgage.payoff_time_months,
            total_term_interest= 0 if self.total_term_interest is None else round(self.total_term_interest, 2),
            total_term_cost= 0 if self.total_term_cost is None else round(self.total_term_cost, 2),
            total_remaining= 0 if self.total_remaining is None else round(self.total_remaining, 2),
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
            
        self.new_mortgage = CanadianMortgageCalculator(self.new_principal, self.new_rate, self.new_term_amortization)
        self.new_mortgage_schedule = (
            self.new_mortgage.create_full_amortization_schedule(extra_annual_payment=self.extra_annual_payment)
        )
        
        # Handle case where schedule might be empty or shorter than term
        if len(self.new_mortgage_schedule) == 0:
            self.total_term_interest = 0
            self.total_term_cost = 0
            self.total_remaining = 0
        else:
            end_of_term_idx = min(self.new_term*12, len(self.new_mortgage_schedule)-1)
            end_of_term = self.new_mortgage_schedule.iloc[end_of_term_idx]
            self.total_term_interest = end_of_term['Cumulative_Interest']
            self.total_term_cost = end_of_term['Cumulative_Principal']
            self.total_remaining = self.new_mortgage.balance_at_renewal
        
        self.combine_results()