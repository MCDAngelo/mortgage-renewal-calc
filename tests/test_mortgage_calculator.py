"""
Tests for CanadianMortgageCalculator class.

Tests the core mortgage calculation functionality including:
- Payment calculations with Canadian semi-annual compounding
- Amortization schedule generation
- Balance tracking
- Date handling
"""

import pytest
from datetime import datetime
from canadian_mortgage_calculator import CanadianMortgageCalculator
import pandas as pd


class TestCanadianMortgagePaymentCalculation:
    """Test Canadian mortgage payment calculations with semi-annual compounding."""
    
    def test_semi_annual_compounding_formula(self):
        """Verify Canadian semi-annual compounding is correctly implemented."""
        mortgage = CanadianMortgageCalculator(
            original_principal=300000,
            annual_rate=0.05,
            amortization_months=300,
            term_months=60,
            start_date=datetime(2024, 1, 1),
            verbose=False
        )
        
        # Calculate expected monthly rate using Canadian method
        semi_annual_rate = 0.05 / 2
        effective_annual_rate = (1 + semi_annual_rate)**2 - 1
        expected_monthly_rate = (1 + effective_annual_rate)**(1/12) - 1
        
        actual_monthly_rate = mortgage.get_effective_monthly_rate()
        assert abs(actual_monthly_rate - expected_monthly_rate) < 0.0000001
    
    def test_payment_with_various_rates(self):
        """Test payment calculation with different interest rates."""
        test_cases = [
            (500000, 0.03, 300),  # 3% rate
            (500000, 0.05, 300),  # 5% rate
            (500000, 0.07, 300),  # 7% rate
        ]
        
        for principal, rate, months in test_cases:
            mortgage = CanadianMortgageCalculator(
                original_principal=principal,
                annual_rate=rate,
                amortization_months=months,
                term_months=60,
                start_date=datetime(2024, 1, 1),
                verbose=False
            )
            
            # Payment should be positive and reasonable
            assert mortgage.monthly_payment > 0
            assert mortgage.monthly_payment < principal  # Less than full principal
            
            # Higher rates should result in higher payments
            if rate > 0.03:
                mortgage_low = CanadianMortgageCalculator(
                    original_principal=principal,
                    annual_rate=0.03,
                    amortization_months=months,
                    term_months=60,
                    start_date=datetime(2024, 1, 1),
                    verbose=False
                )
                assert mortgage.monthly_payment > mortgage_low.monthly_payment
    
    def test_zero_interest_rate_calculation(self):
        """Test payment calculation with zero interest rate."""
        test_cases = [
            (100000, 60),   # 5 years
            (100000, 120),  # 10 years
            (100000, 300),  # 25 years
        ]
        
        for principal, months in test_cases:
            mortgage = CanadianMortgageCalculator(
                original_principal=principal,
                annual_rate=0.0,
                amortization_months=months,
                term_months=60,
                start_date=datetime(2024, 1, 1),
                verbose=False
            )
            
            expected_payment = principal / months
            assert abs(mortgage.monthly_payment - expected_payment) < 0.01, (
                f"For {months} months: expected ${expected_payment:.2f}, got ${mortgage.monthly_payment:.2f}"
            )
    
    def test_different_amortization_periods(self):
        """Test that longer amortization results in lower payments."""
        principal = 500000
        rate = 0.05
        
        mortgage_5yr = CanadianMortgageCalculator(
            original_principal=principal,
            annual_rate=rate,
            amortization_months=60,
            term_months=60,
            start_date=datetime(2024, 1, 1),
            verbose=False
        )
        
        mortgage_25yr = CanadianMortgageCalculator(
            original_principal=principal,
            annual_rate=rate,
            amortization_months=300,
            term_months=60,
            start_date=datetime(2024, 1, 1),
            verbose=False
        )
        
        # Longer amortization should have lower monthly payment
        assert mortgage_25yr.monthly_payment < mortgage_5yr.monthly_payment


class TestAmortizationSchedule:
    """Test amortization schedule generation and accuracy."""
    
    def test_schedule_structure(self, typical_mortgage):
        """Test that amortization schedule has all required columns."""
        schedule = typical_mortgage.create_full_amortization_schedule()
        
        required_columns = [
            'Payment_Number', 'Date', 'Beginning_Balance', 'Payment_Amount',
            'Principal_Payment', 'Interest_Payment', 'Ending_Balance',
            'Cumulative_Principal', 'Cumulative_Interest', 'Year', 'Month'
        ]
        
        for col in required_columns:
            assert col in schedule.columns, f"Missing column: {col}"
    
    def test_balance_consistency(self, typical_mortgage):
        """Test that balances are consistent across payments."""
        schedule = typical_mortgage.create_full_amortization_schedule()
        
        # First payment should start with original principal
        assert abs(schedule.iloc[0]['Beginning_Balance'] - 500000) < 0.01
        
        # Each payment's beginning balance should equal previous ending balance
        for i in range(1, min(20, len(schedule))):
            prev_ending = schedule.iloc[i-1]['Ending_Balance']
            curr_beginning = schedule.iloc[i]['Beginning_Balance']
            assert abs(prev_ending - curr_beginning) < 0.01, (
                f"Payment {i}: Previous ending ${prev_ending:.2f} ≠ Current beginning ${curr_beginning:.2f}"
            )
    
    def test_payment_splits_principal_and_interest(self, typical_mortgage):
        """Test that each payment is properly split between principal and interest."""
        schedule = typical_mortgage.create_full_amortization_schedule()
        
        for i in range(min(10, len(schedule))):
            payment = schedule.iloc[i]
            principal = payment['Principal_Payment']
            interest = payment['Interest_Payment']
            total = payment['Payment_Amount']
            
            # Principal + Interest should equal total payment (within rounding)
            assert abs(principal + interest - total) < 0.02
            
            # Both should be positive
            assert principal >= 0
            assert interest >= 0
    
    def test_total_principal_paid(self, typical_mortgage):
        """Test that total principal paid equals original mortgage amount."""
        schedule = typical_mortgage.create_full_amortization_schedule()
        
        total_principal = schedule['Principal_Payment'].sum()
        total_extra = schedule['Extra_Annual_Payment'].sum()
        
        # Total principal + extra should approximately equal original principal
        assert abs(total_principal + total_extra - 500000) < 5
    
    def test_interest_decreases_over_time(self, typical_mortgage):
        """Test that interest payments decrease as principal is paid down."""
        schedule = typical_mortgage.create_full_amortization_schedule()
        
        # Interest in payment 1 should be greater than payment 60
        first_interest = schedule.iloc[0]['Interest_Payment']
        later_interest = schedule.iloc[59]['Interest_Payment'] if len(schedule) > 59 else schedule.iloc[-1]['Interest_Payment']
        
        assert first_interest > later_interest


class TestPaymentDates:
    """Test payment date calculations and scheduling."""
    
    def test_first_payment_date(self):
        """Test that first payment is exactly 1 month after start date."""
        mortgage = CanadianMortgageCalculator(
            original_principal=500000,
            annual_rate=0.05,
            amortization_months=300,
            term_months=60,
            start_date=datetime(2024, 1, 15),
            verbose=False
        )
        schedule = mortgage.create_full_amortization_schedule()
        first_payment_date = pd.to_datetime(schedule.iloc[0]['Date'])
        
        assert first_payment_date.year == 2024
        assert first_payment_date.month == 2
        assert first_payment_date.day == 15
    
    def test_year_end_rollover(self):
        """Test payment dates roll over correctly from December to January."""
        mortgage = CanadianMortgageCalculator(
            original_principal=500000,
            annual_rate=0.05,
            amortization_months=300,
            term_months=60,
            start_date=datetime(2023, 12, 20),
            verbose=False
        )
        schedule = mortgage.create_full_amortization_schedule()
        first_payment_date = pd.to_datetime(schedule.iloc[0]['Date'])
        
        assert first_payment_date.year == 2024
        assert first_payment_date.month == 1
        assert first_payment_date.day == 20
    
    def test_monthly_payment_sequence(self):
        """Test that payments are scheduled monthly."""
        mortgage = CanadianMortgageCalculator(
            original_principal=500000,
            annual_rate=0.05,
            amortization_months=300,
            term_months=60,
            start_date=datetime(2024, 1, 1),
            verbose=False
        )
        schedule = mortgage.create_full_amortization_schedule()
        
        # Check that year and month increment properly for first 13 payments
        for i in range(min(13, len(schedule))):
            payment = schedule.iloc[i]
            # Payment month starts at 2 (February) when mortgage starts in January
            expected_month = ((2 + i - 1) % 12) + 1
            expected_year = 2024 if i < 11 else 2025
            
            assert payment['Month'] == expected_month, (
                f"Payment {i}: expected month {expected_month}, got {payment['Month']}"
            )
            assert payment['Year'] == expected_year


class TestBalanceCalculations:
    """Test mortgage balance calculations."""
    
    def test_balance_at_renewal(self, large_mortgage):
        """Test that balance at renewal is correctly calculated."""
        schedule = large_mortgage.create_full_amortization_schedule()
        
        # Balance at renewal should be set
        assert large_mortgage.balance_at_renewal > 0
        assert large_mortgage.balance_at_renewal < large_mortgage.original_principal
        
        # Should match the ending balance at term end
        term_end_balance = schedule.iloc[59]['Ending_Balance']
        assert abs(large_mortgage.balance_at_renewal - term_end_balance) < 0.01
    
    def test_calculate_balance_after_payments(self, typical_mortgage):
        """Test balance calculation after specific number of payments."""
        # Calculate balance using the method
        balance_after_12 = typical_mortgage.calculate_balance_after_payments(12)
        
        # Create schedule and compare
        schedule = typical_mortgage.create_full_amortization_schedule()
        schedule_balance = schedule.iloc[11]['Ending_Balance']
        
        # Should be close (might differ slightly due to rounding)
        assert abs(balance_after_12 - schedule_balance) < 1
    
    def test_balance_decreases_monotonically(self, typical_mortgage):
        """Test that balance decreases with each payment."""
        schedule = typical_mortgage.create_full_amortization_schedule()
        
        # Balance should decrease with each payment
        for i in range(1, min(60, len(schedule))):
            prev_balance = schedule.iloc[i-1]['Ending_Balance']
            curr_balance = schedule.iloc[i]['Ending_Balance']
            assert curr_balance <= prev_balance

