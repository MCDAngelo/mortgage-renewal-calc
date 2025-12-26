"""
Tests for extra payment features.

Tests the handling of extra annual payments and their impact on:
- Balance reduction
- Interest savings
- Payoff timeline
"""

import pytest
from datetime import datetime
from canadian_mortgage_calculator import CanadianMortgageCalculator


class TestExtraPayments:
    """Test extra payment features (annual lump sum payments)."""
    
    def test_extra_annual_payment_applied(self):
        """Test that extra annual payments are correctly applied."""
        mortgage = CanadianMortgageCalculator(
            original_principal=400000,
            annual_rate=0.04,
            amortization_months=300,
            term_months=60,
            start_date=datetime(2024, 1, 1),
            verbose=False
        )
        extra_annual = 12000
        schedule = mortgage.create_full_amortization_schedule(extra_annual_payment=extra_annual)
        
        # Each month should show the extra payment
        extra_monthly = round(extra_annual / 12, 2)
        for i in range(min(12, len(schedule))):
            assert abs(schedule.iloc[i]['Extra_Annual_Payment'] - extra_monthly) < 0.01
    
    def test_extra_payments_reduce_balance(self):
        """Test that extra payments reduce balance faster."""
        principal = 400000
        rate = 0.04
        months = 300
        extra_annual = 20000
        
        mortgage_no_extra = CanadianMortgageCalculator(
            original_principal=principal,
            annual_rate=rate,
            amortization_months=months,
            term_months=60,
            start_date=datetime(2024, 1, 1),
            verbose=False
        )
        schedule_no_extra = mortgage_no_extra.create_full_amortization_schedule(extra_annual_payment=0)
        
        mortgage_with_extra = CanadianMortgageCalculator(
            original_principal=principal,
            annual_rate=rate,
            amortization_months=months,
            term_months=60,
            start_date=datetime(2024, 1, 1),
            verbose=False
        )
        schedule_with_extra = mortgage_with_extra.create_full_amortization_schedule(extra_annual_payment=extra_annual)
        
        # Balance after 12 months should be lower with extra payments
        balance_no_extra = schedule_no_extra.iloc[11]['Ending_Balance']
        balance_with_extra = schedule_with_extra.iloc[11]['Ending_Balance']
        
        assert balance_with_extra < balance_no_extra
        # Difference should be AT LEAST the extra amount paid (actually more due to interest savings)
        balance_difference = balance_no_extra - balance_with_extra
        assert balance_difference >= extra_annual, (
            f"Extra payments should reduce balance by at least ${extra_annual:,.2f}, "
            f"but difference was only ${balance_difference:,.2f}"
        )
        # Should not be unreasonably higher (interest savings should be < 5% of extra payment)
        assert balance_difference < extra_annual * 1.05
    
    def test_balance_consistency_with_extra_payments(self):
        """Test balance consistency when extra payments are applied."""
        mortgage = CanadianMortgageCalculator(
            original_principal=400000,
            annual_rate=0.04,
            amortization_months=300,
            term_months=60,
            start_date=datetime(2024, 1, 1),
            verbose=False
        )
        extra_annual = 10000
        schedule = mortgage.create_full_amortization_schedule(extra_annual_payment=extra_annual)
        
        # Each payment's beginning balance should equal previous ending balance
        for i in range(1, min(20, len(schedule))):
            prev_ending = schedule.iloc[i-1]['Ending_Balance']
            curr_beginning = schedule.iloc[i]['Beginning_Balance']
            assert abs(prev_ending - curr_beginning) < 0.01, (
                f"Payment {i}: Previous ending ${prev_ending:.2f} ≠ Current beginning ${curr_beginning:.2f}"
            )
    
    @pytest.mark.slow
    def test_extra_payments_accelerate_payoff(self):
        """Test that extra payments significantly reduce payoff time."""
        principal = 400000
        rate = 0.05
        months = 300
        extra_annual = 40000  # 10% of principal annually
        
        mortgage_no_extra = CanadianMortgageCalculator(
            original_principal=principal,
            annual_rate=rate,
            amortization_months=months,
            term_months=60,
            start_date=datetime(2024, 1, 1),
            verbose=False
        )
        schedule_no_extra = mortgage_no_extra.create_full_amortization_schedule(extra_annual_payment=0)
        
        mortgage_with_extra = CanadianMortgageCalculator(
            original_principal=principal,
            annual_rate=rate,
            amortization_months=months,
            term_months=60,
            start_date=datetime(2024, 1, 1),
            verbose=False
        )
        schedule_with_extra = mortgage_with_extra.create_full_amortization_schedule(extra_annual_payment=extra_annual)
        
        payoff_no_extra = len(schedule_no_extra)
        payoff_with_extra = len(schedule_with_extra)
        
        # Should pay off significantly faster
        assert payoff_with_extra < payoff_no_extra
        # Should save at least 5 years (60 months) with 10% annual extra payments
        assert payoff_no_extra - payoff_with_extra > 60

