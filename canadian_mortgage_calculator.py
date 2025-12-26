import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class CanadianMortgageCalculator:
    def __init__(self, original_principal, annual_rate, amortization_months, 
                 term_months=60, start_date=None, mortgage_gap=(None, None), verbose=False):
        """
        Initialize Canadian mortgage calculator with semi-annual compounding.
        
        Args:
            original_principal: Original mortgage amount
            annual_rate: Annual interest rate (as decimal, e.g., 0.05 for 5%)
            amortization_months: Total amortization period in months (e.g., 300 for 25 years)
            term_months: Current term length in months (default 60 for 5 years)
            start_date: Start date for the mortgage (default: today)
            mortgage_gap: Tuple of (start_date, end_date) for the mortgage gap (default: (None, None))
            verbose: Whether to logger.info verbose output (default: False)
        """
        self.original_principal = original_principal
        self.annual_rate = annual_rate
        self.amortization_months = amortization_months
        self.term_months = term_months
        self.start_date = start_date or datetime.now()
        self.term_end_date = self.start_date + timedelta(days=term_months*30)
        self.verbose = verbose
        self.mortgage_gap = mortgage_gap
        self.balance_at_renewal = 0
        self.payoff_time_months = 0

        # Calculate monthly payment using Canadian semi-annual compounding
        self.monthly_payment = self.calculate_payment(
            amortization_months
        )
        
        if verbose:
            logger.info(f"Mortgage Details:")
            logger.info(f"Original Principal: ${self.original_principal:,.2f}")
            logger.info(f"Annual Rate: {self.annual_rate:.4%}")
            logger.info(f"Amortization: {self.amortization_months} months ({self.amortization_months/12:.0f} years)")
            logger.info(f"Monthly Payment: ${self.monthly_payment:,.2f}")
            logger.info(f"Mortgage Gap: {self.mortgage_gap[0]} to {self.mortgage_gap[1]}")


    def calculate_payment(self, amortization_months):
        """
        Calculate monthly payment using Canadian semi-annual compounding.
        
        In Canada, mortgage rates are compounded semi-annually but paid monthly.
        This requires converting the annual rate to an effective monthly rate.
        """
        if self.annual_rate == 0:
            return self.original_principal / amortization_months
        
        monthly_rate = self.get_effective_monthly_rate()
        
        payment = round(self.original_principal * (monthly_rate * (1 + monthly_rate)**amortization_months) / \
                  ((1 + monthly_rate)**amortization_months - 1), 2)
        return payment
    
    def get_effective_monthly_rate(self):
        """Get the effective monthly rate used in Canadian mortgages."""
        semi_annual_rate = self.annual_rate / 2
        effective_annual_rate = (1 + semi_annual_rate)**2 - 1
        monthly_rate = (1 + effective_annual_rate)**(1/12) - 1
        return monthly_rate
    
    def calculate_balance_after_payments(self, num_payments):
        """Calculate remaining balance after a specific number of payments."""
        monthly_rate = self.get_effective_monthly_rate()
        
        if self.annual_rate == 0:
            return max(0, self.original_principal - (self.monthly_payment * num_payments))
        
        # Standard mortgage balance formula
        balance = round(self.original_principal * (1 + monthly_rate)**num_payments - \
                 self.monthly_payment * (((1 + monthly_rate)**num_payments - 1) / monthly_rate), 2)
        
        return max(0, balance)
    
    def create_full_amortization_schedule(self, extra_annual_payment=0):
        """
        Create complete amortization schedule matching Canadian bank format.
        
        Args:
            extra_payment: Additional monthly payment toward principal
            
        Returns:
            DataFrame with detailed payment breakdown
        """

        if self.mortgage_gap[0] is not None:
            mortgage_gap = True
            gap_start_date = self.mortgage_gap[0]
            gap_end_date = self.mortgage_gap[1]
        else:
            mortgage_gap = False
            
        schedule = []
        balance = self.original_principal
        monthly_rate = self.get_effective_monthly_rate()
        total_monthly_payment = self.monthly_payment
        extra_annual_payment_per_month = round(extra_annual_payment / 12, 2)
        cumulative_interest = 0
        cumulative_principal = 0

        logger.debug(f"Original Principal: ${self.original_principal:,.2f}")
        logger.debug(f"Annual Rate: {self.annual_rate:.4%}")
        logger.debug(f"Monthly Rate: {monthly_rate:.6%}")
        logger.debug(f"Total Monthly Payment: ${total_monthly_payment:,.2f}")

        # Start at first payment date (1 month after start)
        if self.start_date.month == 12:
            current_date = self.start_date.replace(year=self.start_date.year + 1, month=1)
        else:
            current_date = self.start_date.replace(month=self.start_date.month + 1)
        
        for payment_num in range(1, self.amortization_months + 1):
            if balance <= 0.01:  # Account for rounding
                break

            if mortgage_gap:
                if current_date >= gap_start_date and current_date <= gap_end_date:
                    total_monthly_payment = 0
                else:
                    total_monthly_payment = self.monthly_payment
            
            # Calculate interest for this payment
            interest_payment = round(balance * monthly_rate, 2)
            logger.debug(f"Interest Payment: ${interest_payment:,.2f}")
            
            # Calculate principal payment (ensuring we don't overpay)
            principal_payment = round(min(total_monthly_payment - interest_payment, balance), 2)
            logger.debug(f"Principal Payment: ${principal_payment:,.2f}")   
            
            # Actual payment amount (might be less than scheduled on final payment)
            actual_payment = interest_payment + principal_payment
            logger.debug(f"Actual Payment: ${actual_payment:,.2f}")
            # Update balance
            balance -= round((principal_payment + extra_annual_payment_per_month), 2)
            logger.debug(f"Balance: ${balance:,.2f}")

            # Update cumulative totals
            cumulative_interest += interest_payment
            cumulative_principal += round((principal_payment + extra_annual_payment_per_month), 2)
            
            # Add to schedule
            schedule.append({
                'Payment_Number': payment_num,
                'Date': current_date.strftime('%Y-%m-%d'),
                'Beginning_Balance': round(balance + principal_payment + extra_annual_payment_per_month, 2),
                'Payment_Amount': round(actual_payment, 2),
                'Principal_Payment': round(principal_payment, 2),
                'Extra_Annual_Payment': round(extra_annual_payment_per_month, 2),
                'Interest_Payment': round(interest_payment, 2),
                'Ending_Balance': round(balance, 2),
                'Cumulative_Principal': round(cumulative_principal, 2),
                'Cumulative_Interest': round(cumulative_interest, 2),
                'Year': current_date.year,
                'Month': current_date.month
            })
            if payment_num == self.term_months:
                self.balance_at_renewal = balance
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
            
            if balance <= 0.01:
                self.payoff_time_months = payment_num
                break
        
        return pd.DataFrame(schedule)
    
    def create_annual_summary(self, schedule_df):
        """Create annual summary of principal and interest payments."""
        if schedule_df.empty:
            return pd.DataFrame()
        
        annual_summary = schedule_df.groupby('Year').agg({
            'Principal_Payment': 'sum',
            'Interest_Payment': 'sum',
            'Payment_Amount': 'sum',
            'Ending_Balance': 'last'  # Balance at end of year
        }).round(2)
        
        annual_summary['Total_Payment'] = annual_summary['Principal_Payment'] + annual_summary['Interest_Payment']
        annual_summary['Principal_Percentage'] = (annual_summary['Principal_Payment'] / annual_summary['Total_Payment'] * 100).round(1)
        annual_summary['Interest_Percentage'] = (annual_summary['Interest_Payment'] / annual_summary['Total_Payment'] * 100).round(1)
        
        # Rename columns for clarity
        annual_summary.columns = [
            'Principal_Paid', 'Interest_Paid', 'Last_Payment', 'Year_End_Balance', 
            'Total_Payments', 'Principal_%', 'Interest_%'
        ]
        
        return annual_summary
    
    def print_mortgage_summary(self, schedule_df):
        """Print a comprehensive mortgage summary like banks provide."""
        if schedule_df.empty:
            logger.info("No payment schedule available.")
            return

        self.total_payments_in_term = len(schedule_df[0:self.term_months])
        self.total_interest = schedule_df[0:self.term_months]['Interest_Payment'].sum()
        self.total_principal = schedule_df[0:self.term_months]['Principal_Payment'].sum()
        self.total_paid = self.total_interest + self.total_principal
        self.total_payments_to_payoff = len(schedule_df)

        if self.verbose:
            logger.info(f"Original Mortgage Amount: ${self.original_principal:,.2f}")
            logger.info(f"Interest Rate (Annual): {self.annual_rate:.4%}")
            logger.info(f"Effective Monthly Rate: {self.get_effective_monthly_rate():.6%}")
            logger.info(f"Amortization Period: {self.amortization_months} months ({self.amortization_months/12:.0f} years)")
            logger.info(f"Monthly Payment: ${self.monthly_payment:,.2f}")
            logger.info(f"Total Number of Payments in Term: {self.total_payments_in_term}")
            logger.info(f"Total Interest Paid: ${self.total_interest:,.2f}")
            logger.info(f"Total Principal Paid: ${self.total_principal:,.2f}")
            logger.info(f"Total Amount Paid: ${self.total_paid:,.2f}")
            logger.info(f"Interest as % of Total: {(self.total_interest/self.total_paid)*100:.1f}%")
            logger.info(f"Remaining Balance: ${self.calculate_balance_after_payments(self.term_months):,.2f}")
            logger.info(f"Total Number of Payments to Payoff: {self.total_payments_to_payoff}")            
    
    def verify_calculation(self, expected_payment):
        """Verify if calculated payment matches expected payment."""
        difference = abs(self.monthly_payment - expected_payment)
        percentage_diff = (difference / expected_payment) * 100

        logger.info(f"Calculated Payment: ${self.monthly_payment:,.2f}")
        logger.info(f"Expected Payment: ${expected_payment:,.2f}")
        logger.info(f"Difference: ${difference:,.2f} ({percentage_diff:.3f}%)")
        
        if difference < 0.01:
            logger.info("✓ MATCH: Payments match within 1 cent")
        elif difference < 1.00:
            logger.info("⚠ CLOSE: Difference likely due to rounding")
        else:
            logger.info("✗ MISMATCH: Significant difference - check inputs")
        
        return difference < 1.00

