"""
Pytest configuration and shared fixtures for mortgage calculator tests.

This file is automatically loaded by pytest and provides:
- Common fixtures used across multiple test files
- Test configuration
- Shared test data
"""

import pytest
from datetime import datetime
from canadian_mortgage_calculator import CanadianMortgageCalculator
from mortgage_renewal import MortgageRenewalPlanner


@pytest.fixture
def typical_mortgage():
    """Fixture providing a typical Canadian mortgage instance."""
    return CanadianMortgageCalculator(
        original_principal=500000,
        annual_rate=0.05,
        amortization_months=300,  # 25 years
        term_months=60,  # 5 years
        start_date=datetime(2024, 1, 1),
        verbose=False
    )


@pytest.fixture
def large_mortgage():
    """Fixture providing a large mortgage for testing renewal scenarios."""
    return CanadianMortgageCalculator(
        original_principal=700000,
        annual_rate=0.0199,
        amortization_months=360,  # 30 years
        term_months=60,  # 5 years
        start_date=datetime(2020, 1, 1),
        verbose=False
    )


@pytest.fixture
def mortgage_with_schedule(typical_mortgage):
    """Fixture providing a mortgage with its amortization schedule already generated."""
    schedule = typical_mortgage.create_full_amortization_schedule()
    return typical_mortgage, schedule


@pytest.fixture
def renewal_planner(large_mortgage):
    """Fixture providing a renewal planner with a sample mortgage."""
    large_mortgage.create_full_amortization_schedule()
    return MortgageRenewalPlanner(large_mortgage)


@pytest.fixture
def sample_renewal_scenarios():
    """Fixture providing common renewal scenario configurations."""
    return [
        {
            'name': 'Low rate - no paydown',
            'new_rate': 0.035,
            'principal_paydown': 0,
            'extra_monthly_payment': 0,
            'extra_annual_payment': 0,
        },
        {
            'name': 'Medium rate - $100k paydown',
            'new_rate': 0.045,
            'principal_paydown': 100000,
            'extra_monthly_payment': 0,
            'extra_annual_payment': 0,
        },
        {
            'name': 'High rate - aggressive paydown',
            'new_rate': 0.055,
            'principal_paydown': 150000,
            'extra_monthly_payment': 500,
            'extra_annual_payment': 20000,
        },
    ]


# Configure pytest markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )

