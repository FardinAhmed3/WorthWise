"""Core calculation engine for ROI and financial metrics"""

import numpy as np
from src.data.constants import ROOMMATE_REDUCTION_RATE, MAX_ROOMMATE_DISCOUNT, COMFORT_WEIGHTS
from typing import Tuple, Optional


def calculate_total_cost_of_attendance(
    tuition: float,
    housing: float,
    food: float,
    transport: float,
    books: float,
    misc: float,
    roommate_count: int = 0
) -> float:
    """
    Calculate total yearly cost of attendance with roommate adjustment.
    
    Args:
        tuition: Annual tuition and fees
        housing: Annual housing cost
        food: Annual food budget
        transport: Annual transportation cost
        books: Annual books and supplies
        misc: Annual miscellaneous expenses
        roommate_count: Number of roommates (0-3)
    
    Returns:
        Total annual cost of attendance
    """
    # Apply roommate discount to housing (25% reduction per roommate, max 75%)
    roommate_discount = min(roommate_count * ROOMMATE_REDUCTION_RATE, MAX_ROOMMATE_DISCOUNT)
    adjusted_housing = housing * (1 - roommate_discount)
    
    total_cost = tuition + adjusted_housing + food + transport + books + misc
    return max(0, total_cost)  # Ensure non-negative


def calculate_cumulative_debt(
    yearly_cost: float,
    grants: float,
    scholarships: float,
    work_study: float,
    family_contribution: float,
    years: int = 4
) -> float:
    """
    Calculate total debt at graduation.
    
    Args:
        yearly_cost: Annual cost of attendance
        grants: Annual grants (non-repayable)
        scholarships: Annual scholarships (non-repayable)
        work_study: Annual work-study earnings
        family_contribution: Annual family contribution
        years: Number of years (default 4)
    
    Returns:
        Total cumulative debt at graduation
    """
    yearly_aid = grants + scholarships + work_study + family_contribution
    yearly_debt = max(0, yearly_cost - yearly_aid)
    total_debt = yearly_debt * years
    return total_debt


def calculate_loan_payment(
    principal: float,
    annual_rate: float,
    years: int = 10
) -> float:
    """
    Calculate monthly loan payment using standard amortization formula.
    
    Args:
        principal: Loan principal amount
        annual_rate: Annual interest rate (e.g., 0.055 for 5.5%)
        years: Loan term in years (default 10)
    
    Returns:
        Monthly payment amount
    """
    if principal <= 0:
        return 0.0
    
    if annual_rate <= 0:
        # No interest case
        return principal / (years * 12)
    
    monthly_rate = annual_rate / 12
    num_payments = years * 12
    
    # Standard amortization formula: P * [r(1+r)^n] / [(1+r)^n - 1]
    monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                     ((1 + monthly_rate) ** num_payments - 1)
    
    return monthly_payment


def calculate_earnings_projection(
    year1_salary: float,
    growth_rate: float = 0.03
) -> Tuple[float, float, float]:
    """
    Project earnings for years 1, 3, and 5 post-graduation.
    
    Args:
        year1_salary: First year post-graduation salary
        growth_rate: Annual salary growth rate (default 3%)
    
    Returns:
        Tuple of (year1, year3, year5) earnings
    """
    year1 = year1_salary
    year3 = year1_salary * ((1 + growth_rate) ** 2)
    year5 = year1_salary * ((1 + growth_rate) ** 4)
    
    return (year1, year3, year5)


def calculate_roi(
    total_cost: float,
    year5_earnings: float,
    baseline_earnings: float = 35000
) -> float:
    """
    Calculate Return on Investment (ROI) percentage.
    
    Formula: [(5yr_cumulative_earnings - 5yr_baseline - total_cost) / total_cost] * 100
    
    Args:
        total_cost: Total cost of degree (4 years)
        year5_earnings: Projected year 5 salary
        baseline_earnings: Baseline earnings without degree (default $35k)
    
    Returns:
        ROI as percentage
    """
    if total_cost <= 0:
        return 0.0
    
    # Estimate 5-year cumulative earnings using average of year 1 and year 5
    # Simplified: assume linear growth from year1 to year5
    # year1 = year5 / (1.03^4) ≈ year5 / 1.126
    year1_estimate = year5_earnings / 1.126
    avg_earnings = (year1_estimate + year5_earnings) / 2
    five_year_earnings = avg_earnings * 5
    
    # Baseline earnings over 5 years
    five_year_baseline = baseline_earnings * 5
    
    # Net benefit
    net_benefit = five_year_earnings - five_year_baseline - total_cost
    
    roi = (net_benefit / total_cost) * 100
    return roi


def calculate_payback_period(
    total_debt: float,
    annual_salary: float,
    payment_rate: float = 0.10
) -> float:
    """
    Calculate years to pay off debt at specified payment rate of gross income.
    
    Args:
        total_debt: Total debt at graduation
        annual_salary: First year post-graduation salary
        payment_rate: Fraction of gross income for debt payment (default 10%)
    
    Returns:
        Years to pay off debt
    """
    if total_debt <= 0:
        return 0.0
    
    if annual_salary <= 0:
        return float('inf')
    
    annual_payment = annual_salary * payment_rate
    
    if annual_payment <= 0:
        return float('inf')
    
    # Simple calculation: debt / annual_payment
    # (Does not account for interest, simplified for MVP)
    years = total_debt / annual_payment
    
    return min(years, 50)  # Cap at 50 years for display purposes


def calculate_dti_ratio(
    monthly_debt_payment: float,
    monthly_income: float
) -> float:
    """
    Calculate Debt-to-Income ratio as percentage.
    
    Args:
        monthly_debt_payment: Monthly debt payment amount
        monthly_income: Monthly gross income
    
    Returns:
        DTI ratio as percentage (0-100+)
    """
    if monthly_income <= 0:
        return 0.0
    
    dti = (monthly_debt_payment / monthly_income) * 100
    return min(dti, 100)  # Cap at 100% for comfort index calculation


def calculate_comfort_index(
    dti: float,
    graduation_rate: float,
    roi: float
) -> float:
    """
    Calculate Financial Comfort Index (0-100) based on weighted factors.
    
    Weights:
    - DTI: 40% (lower is better)
    - Graduation Rate: 30% (higher is better)
    - ROI: 30% (higher is better)
    
    Args:
        dti: Debt-to-income ratio (0-100+)
        graduation_rate: Graduation rate (0-1)
        roi: Return on investment percentage
    
    Returns:
        Comfort index score (0-100)
    """
    # Normalize DTI (invert so lower is better, cap at 50%)
    # DTI of 0% = 100 points, DTI of 50%+ = 0 points
    dti_score = max(0, 100 - (dti * 2))
    
    # Normalize graduation rate (0-1 to 0-100)
    grad_score = graduation_rate * 100
    
    # Normalize ROI (scale to 0-100)
    # ROI of 100%+ = 100 points, ROI of -100% = 0 points
    roi_score = max(0, min(100, (roi + 100) / 2))
    
    # Weighted average
    comfort_index = (
        dti_score * COMFORT_WEIGHTS['dti'] +
        grad_score * COMFORT_WEIGHTS['graduation_rate'] +
        roi_score * COMFORT_WEIGHTS['roi']
    )
    
    return max(0, min(100, comfort_index))


def calculate_net_price(
    sticker_price: float,
    grants: float,
    scholarships: float
) -> float:
    """
    Calculate net price after grants and scholarships.
    
    Args:
        sticker_price: Published tuition and fees
        grants: Annual grants
        scholarships: Annual scholarships
    
    Returns:
        Net price after aid
    """
    net = sticker_price - grants - scholarships
    return max(0, net)


def calculate_monthly_budget(
    annual_salary: float,
    tax_rate: float = 0.22
) -> float:
    """
    Calculate monthly take-home pay after taxes.
    
    Args:
        annual_salary: Gross annual salary
        tax_rate: Effective tax rate (default 22%)
    
    Returns:
        Monthly take-home pay
    """
    annual_take_home = annual_salary * (1 - tax_rate)
    monthly_take_home = annual_take_home / 12
    return monthly_take_home


def format_currency(amount: float) -> str:
    """Format amount as USD currency string."""
    return f"${amount:,.0f}"


def format_percentage(value: float) -> str:
    """Format value as percentage string."""
    return f"{value:.1f}%"


def format_years(years: float) -> str:
    """Format years with one decimal place."""
    if years == float('inf'):
        return "Never"
    return f"{years:.1f} years"

