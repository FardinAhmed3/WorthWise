"""
ROI Calculator Service
Core business logic for ROI, debt, earnings, and financial comfort calculations
"""

from typing import Dict, Any, Optional, Tuple, List
import math


class ROICalculator:
    """
    Calculate Return on Investment and related financial metrics
    for college education scenarios
    """
    
    # Default assumptions
    DEFAULT_PROGRAM_YEARS = 4
    DEFAULT_FOOD_MONTHLY = 0
    DEFAULT_TRANSPORT_MONTHLY = 0
    DEFAULT_BOOKS_ANNUAL = 0
    DEFAULT_MISC_MONTHLY = 0
    DEFAULT_UTILITIES_MONTHLY = 0
    
    def __init__(self):
        """Initialize ROI Calculator"""
        pass
    
    def calculate_total_cost(
        self,
        tuition_annual: int,
        housing_annual: int,
        food_monthly: int,
        transport_monthly: int,
        utilities_monthly: int,
        misc_monthly: int,
        books_annual: int
    ) -> Tuple[int, int, int]:
        """
        Calculate total annual cost
        
        Returns:
            Tuple of (true_yearly_cost, housing_annual, other_expenses)
        """
        food_annual = food_monthly * 12
        transport_annual = transport_monthly * 12
        utilities_annual = utilities_monthly * 12
        misc_annual = misc_monthly * 12
        
        other_expenses = (
            food_annual +
            transport_annual +
            utilities_annual +
            misc_annual +
            books_annual
        )
        
        true_yearly_cost = tuition_annual + housing_annual + other_expenses
        
        return true_yearly_cost, housing_annual, other_expenses
    
    def calculate_debt(
        self,
        yearly_cost: int,
        aid_annual: int,
        cash_annual: int,
        program_years: int,
        loan_apr: float
    ) -> int:
        """
        Calculate expected debt at graduation
        
        For unsubsidized federal student loans:
        - Interest accrues as simple interest during school (not compound)
        - Interest capitalizes (is added to principal) at graduation
        - Each year's loan accrues interest for the remaining years until graduation
        
        Args:
            yearly_cost: Annual total cost
            aid_annual: Annual grants/scholarships (non-repayable)
            cash_annual: Annual cash contribution
            loan_apr: Annual loan interest rate
            
        Returns:
            Total debt at graduation (principal + capitalized interest)
        """
        # Annual amount that needs to be borrowed
        annual_need = max(0, yearly_cost - aid_annual - cash_annual)
        
        if annual_need == 0:
            return 0
        
        # Calculate principal (sum of all loans)
        total_principal = annual_need * program_years
        
        # Calculate interest that accrues during school (simple interest, not compound)
        # Each year's loan accrues interest for the remaining years until graduation
        total_interest = 0
        for year in range(program_years):
            years_until_graduation = program_years - year - 1
            # Simple interest: principal * rate * time
            interest_for_this_loan = annual_need * loan_apr * years_until_graduation
            total_interest += interest_for_this_loan
        
        # At graduation, interest capitalizes (is added to principal)
        total_debt_at_grad = total_principal + total_interest
        
        return int(total_debt_at_grad)
    
    def calculate_roi(
        self,
        total_investment: int,
        earnings_year_1: Optional[int] = None,
        earnings_year_3: Optional[int] = None,
        earnings_year_5: Optional[int] = None,
        earnings_year_10: Optional[int] = None
    ) -> Optional[float]:
        """
        Calculate Return on Investment
        
        ROI = (Cumulative Earnings - Total Investment) / Total Investment
        
        Uses earnings data to model earnings growth over time and calculate
        cumulative earnings over a 10-year period.
        
        Args:
            total_investment: Total cost of education (debt + cash + aid)
            earnings_year_1: Earnings 1 year after graduation
            earnings_year_3: Earnings 3 years after graduation
            earnings_year_5: Earnings 5 years after graduation
            earnings_year_10: Earnings 10 years after graduation (optional)
            
        Returns:
            ROI ratio or None if insufficient data
        """
        if total_investment <= 0:
            return None
        
        # Need at least one earnings data point
        if not any([earnings_year_1, earnings_year_3, earnings_year_5, earnings_year_10]):
            return None
        
        # Model earnings growth over 10 years
        # Use available data points to interpolate/extrapolate
        earnings_by_year = {}
        
        if earnings_year_1:
            earnings_by_year[1] = earnings_year_1
        if earnings_year_3:
            earnings_by_year[3] = earnings_year_3
        if earnings_year_5:
            earnings_by_year[5] = earnings_year_5
        if earnings_year_10:
            earnings_by_year[10] = earnings_year_10
        
        # Interpolate missing years using compound growth model
        # Priority: use year 1 and year 5 if available (most accurate)
        if earnings_year_1 and earnings_year_5:
            # Calculate annual growth rate from year 1 to year 5
            if earnings_year_1 > 0:
                growth_rate = (earnings_year_5 / earnings_year_1) ** (1.0 / 4.0) - 1.0
                # Fill in years 2-4
                for year in range(2, 5):
                    if year not in earnings_by_year:
                        earnings_by_year[year] = int(earnings_year_1 * (1 + growth_rate) ** (year - 1))
        elif earnings_year_1 and earnings_year_3:
            # Calculate growth rate from year 1 to year 3
            if earnings_year_1 > 0:
                growth_rate = (earnings_year_3 / earnings_year_1) ** (1.0 / 2.0) - 1.0
                # Extrapolate to year 5
                if 5 not in earnings_by_year:
                    earnings_by_year[5] = int(earnings_year_1 * (1 + growth_rate) ** 4)
        elif earnings_year_3 and earnings_year_5:
            # Calculate growth rate from year 3 to year 5
            if earnings_year_3 > 0:
                growth_rate = (earnings_year_5 / earnings_year_3) ** (1.0 / 2.0) - 1.0
                # Backfill year 1 if missing
                if 1 not in earnings_by_year:
                    earnings_by_year[1] = int(earnings_year_3 / ((1 + growth_rate) ** 2))
        
        # If we only have one data point, assume 3% annual growth (typical wage growth)
        if len(earnings_by_year) == 1:
            single_year = min(earnings_by_year.keys())
            single_earnings = earnings_by_year[single_year]
            growth_rate = 0.03  # 3% annual growth
            
            # Fill in all years
            for year in range(1, 11):
                if year not in earnings_by_year:
                    years_diff = year - single_year
                    earnings_by_year[year] = int(single_earnings * (1 + growth_rate) ** years_diff)
        
        # Ensure we have year 5 for extrapolation
        if 5 not in earnings_by_year:
            if 3 in earnings_by_year and 1 in earnings_by_year:
                # Interpolate from 1 and 3
                if earnings_by_year[1] > 0:
                    growth_rate = (earnings_by_year[3] / earnings_by_year[1]) ** (1.0 / 2.0) - 1.0
                    earnings_by_year[5] = int(earnings_by_year[1] * (1 + growth_rate) ** 4)
            elif 1 in earnings_by_year:
                # Assume 3% growth from year 1
                earnings_by_year[5] = int(earnings_by_year[1] * (1.03) ** 4)
            elif 3 in earnings_by_year:
                # Assume 3% growth from year 3
                earnings_by_year[5] = int(earnings_by_year[3] * (1.03) ** 2)
        
        # If we have year 5 but not year 10, assume slower growth (2% annual after year 5)
        if 5 in earnings_by_year and 10 not in earnings_by_year:
            earnings_by_year[10] = int(earnings_by_year[5] * (1.02) ** 5)
        
        # Fill in years 6-9 with linear interpolation between year 5 and year 10
        if 5 in earnings_by_year and 10 in earnings_by_year:
            for year in range(6, 10):
                if year not in earnings_by_year:
                    # Linear interpolation
                    ratio = (year - 5) / 5.0
                    earnings_by_year[year] = int(
                        earnings_by_year[5] * (1 - ratio) + earnings_by_year[10] * ratio
                    )
        
        # Calculate cumulative earnings over 10 years
        cumulative_earnings = 0
        for year in range(1, 11):
            if year in earnings_by_year:
                cumulative_earnings += earnings_by_year[year]
            elif year - 1 in earnings_by_year:
                # Use previous year if available
                cumulative_earnings += earnings_by_year[year - 1]
            else:
                # Fallback: use first available earnings (shouldn't happen with above logic)
                if earnings_by_year:
                    first_earnings = next(iter(earnings_by_year.values()))
                    cumulative_earnings += first_earnings
        
        # Calculate ROI
        roi = (cumulative_earnings - total_investment) / total_investment
        
        return round(roi, 2)
    
    def calculate_payback_period(
        self,
        total_debt: int,
        earnings_year_1: Optional[int] = None,
        earnings_year_3: Optional[int] = None,
        earnings_year_5: Optional[int] = None,
        effective_tax_rate: float = 0.15,
        loan_apr: float = 0.0529,
        living_expenses_annual: int = 45000,
        tuition_in_state: Optional[int] = None,
        major_category: Optional[str] = None,
        institution_region: Optional[str] = None
    ) -> Optional[float]:
        """
        Calculate debt payback period using robust, production-ready earnings-based approach

        Handles edge cases and missing data with intelligent fallbacks:
        - Uses statistical defaults when earnings data is missing
        - Accounts for major field and regional earnings variations
        - Provides conservative estimates rather than returning None
        - Progressive payment strategy based on career stage

        Payment Strategy (configurable percentages):
        - Year 1: 8% of disposable income (early career conservatism)
        - Years 2-3: 12% of disposable income (career building)
        - Year 4+: 15% of disposable income (career established)

        Args:
            total_debt: Total debt at graduation (principal + capitalized interest)
            earnings_year_1: Year 1 post-grad earnings (actual or None)
            earnings_year_3: Year 3 post-grad earnings (actual or None)
            earnings_year_5: Year 5 post-grad earnings (actual or None)
            effective_tax_rate: Tax rate (decimal, default 0.15)
            loan_apr: Annual loan interest rate (decimal, default 5.29%)
            living_expenses_annual: Annual living expenses (default $45,000)
            tuition_in_state: In-state tuition for regional cost adjustment
            major_category: Major field for earnings estimation fallback
            institution_region: Geographic region for earnings adjustment

        Returns:
            Years to payback (0.5 to 25 years) or None only for impossible cases
        """
        # Input validation and edge case handling
        if total_debt <= 0:
            return 0.0

        if total_debt > 500000:  # Unrealistic debt levels
            return None

        # Validate and normalize inputs
        effective_tax_rate = max(0.0, min(0.5, effective_tax_rate))  # 0-50% range
        loan_apr = max(0.0, min(0.15, loan_apr))  # 0-15% range

        # Adjust living expenses based on tuition cost (regional cost proxy)
        if tuition_in_state and tuition_in_state > 0:
            # High-tuition states tend to have higher living costs
            tuition_factor = min(0.03, tuition_in_state / 100000)  # Max 3% adjustment
            living_expenses_annual = int(living_expenses_annual * (1 + tuition_factor))

        # Build earnings trajectory with intelligent fallbacks
        earnings_trajectory = self._build_earnings_trajectory_with_fallbacks(
            earnings_year_1, earnings_year_3, earnings_year_5,
            major_category, institution_region, tuition_in_state
        )

        # If we still don't have any earnings data, use national averages
        if not any(earnings_trajectory):
            earnings_trajectory = self._get_national_average_trajectory(major_category)

        # If still no data, return None (truly impossible to estimate)
        if not any(earnings_trajectory):
            return None

        remaining_debt = float(total_debt)
        total_months = 0
        max_simulation_years = 25  # Extended from 15 to handle high debt cases

        # Simulate monthly payments over time with progressive payment strategy
        for year in range(1, max_simulation_years + 1):
            if year > len(earnings_trajectory):
                # Extrapolate using final year's earnings with conservative growth
                final_earnings = earnings_trajectory[-1] if earnings_trajectory else 50000
                annual_earnings = int(final_earnings * (1.02) ** (year - len(earnings_trajectory)))
            else:
                annual_earnings = earnings_trajectory[year - 1]

            if not annual_earnings or annual_earnings <= 0:
                annual_earnings = 35000  # Minimum wage fallback

            # Calculate after-tax income with realistic tax brackets
            after_tax_income = self._calculate_effective_after_tax_income(
                annual_earnings, effective_tax_rate
            )

            # Subtract living expenses (ensure minimum disposable income)
            disposable_income = max(1000, after_tax_income - living_expenses_annual)

            # Determine debt payment percentage based on career stage and earnings level
            payment_percentage = self._calculate_payment_percentage(year, annual_earnings, disposable_income)

            annual_payment = disposable_income * payment_percentage

            # Apply minimum payment floor and maximum payment cap
            annual_payment = max(100, min(annual_payment, disposable_income * 0.25))  # 1%-25% range

            # Convert to monthly payment
            monthly_payment = annual_payment / 12.0

            # Apply payments for 12 months
            for month in range(12):
                if remaining_debt <= 0:
                    break

                # Calculate interest for this month
                monthly_interest = remaining_debt * (loan_apr / 12.0)
                remaining_debt += monthly_interest

                # Apply payment to principal
                payment_amount = min(monthly_payment, remaining_debt)
                remaining_debt -= payment_amount
                total_months += 1

                # Early exit if debt is paid off
                if remaining_debt <= 0:
                    break

            if remaining_debt <= 0:
                break

        # If debt still remains after maximum simulation period, return the maximum
        if remaining_debt > 0:
            return float(max_simulation_years)

        # Convert months to years and round up, with minimum 0.5 years
        years = max(0.5, math.ceil(total_months / 12.0))

        return min(years, float(max_simulation_years))

    def _build_earnings_trajectory_with_fallbacks(
        self,
        earnings_year_1: Optional[int],
        earnings_year_3: Optional[int],
        earnings_year_5: Optional[int],
        major_category: Optional[str],
        institution_region: Optional[str],
        tuition_in_state: Optional[int]
    ) -> List[int]:
        """
        Build earnings trajectory with intelligent fallbacks for missing data

        Priority order for earnings estimation:
        1. Actual reported earnings data
        2. Major field averages (STEM vs non-STEM)
        3. Regional adjustments
        4. National averages as final fallback

        Returns:
            List of 25 annual earnings values (never None)
        """
        trajectory = [0] * 25  # Initialize with zeros

        # Set known data points
        if earnings_year_1 and earnings_year_1 > 0:
            trajectory[0] = earnings_year_1
        if earnings_year_3 and earnings_year_3 > 0:
            trajectory[2] = earnings_year_3
        if earnings_year_5 and earnings_year_5 > 0:
            trajectory[4] = earnings_year_5

        # Get fallback earnings levels
        fallback_earnings = self._get_fallback_earnings(
            major_category, institution_region, tuition_in_state
        )

        # Fill missing year 1
        if trajectory[0] == 0:
            trajectory[0] = fallback_earnings.get('year_1', 45000)

        # Fill missing year 3 (interpolate from year 1 if year 5 exists)
        if trajectory[2] == 0:
            if trajectory[4] > 0:
                # Interpolate between year 1 and year 5
                trajectory[2] = int(trajectory[0] + (trajectory[4] - trajectory[0]) * (2/4))
            else:
                trajectory[2] = fallback_earnings.get('year_3', 55000)

        # Fill missing year 5
        if trajectory[4] == 0:
            if trajectory[2] > 0:
                # Extrapolate from year 1-3 trend
                growth_rate = (trajectory[2] / trajectory[0]) ** (1/2) if trajectory[0] > 0 else 1.04
                trajectory[4] = int(trajectory[2] * (growth_rate ** 2))
            else:
                trajectory[4] = fallback_earnings.get('year_5', 70000)

        # Fill years 6-25 using realistic growth patterns
        for year in range(5, 25):
            if trajectory[year] == 0:
                # Use progressive growth rates based on career stage
                if year <= 7:  # Years 6-8: 4-6% growth (rapid advancement)
                    growth_rate = 0.05
                elif year <= 12:  # Years 9-13: 3-4% growth (steady advancement)
                    growth_rate = 0.035
                elif year <= 17:  # Years 14-18: 2-3% growth (mid-career)
                    growth_rate = 0.025
                else:  # Years 19+: 1-2% growth (senior level)
                    growth_rate = 0.015

                trajectory[year] = int(trajectory[year - 1] * (1 + growth_rate))

        return trajectory

    def _get_fallback_earnings(
        self,
        major_category: Optional[str],
        institution_region: Optional[str],
        tuition_in_state: Optional[int]
    ) -> Dict[str, int]:
        """
        Get statistically reasonable fallback earnings based on major and region

        Uses research-based averages for different fields and regions
        """
        # Base national averages by major category
        major_averages = {
            'stem': {'year_1': 65000, 'year_3': 85000, 'year_5': 105000},
            'business': {'year_1': 55000, 'year_3': 70000, 'year_5': 90000},
            'healthcare': {'year_1': 60000, 'year_3': 75000, 'year_5': 95000},
            'education': {'year_1': 40000, 'year_3': 48000, 'year_5': 55000},
            'humanities': {'year_1': 38000, 'year_3': 45000, 'year_5': 52000},
            'trades': {'year_1': 45000, 'year_3': 55000, 'year_5': 65000},
        }

        # Regional adjustment factors (cost of living + opportunity)
        regional_factors = {
            'northeast': 1.08,  # Higher cost, higher pay
            'west': 1.06,       # High cost areas
            'south': 0.92,      # Lower cost of living
            'midwest': 0.96,    # Moderate
        }

        # Determine major category
        category = 'business'  # Default
        if major_category:
            major_lower = major_category.lower()
            if any(term in major_lower for term in ['computer', 'engineering', 'math', 'science', 'technology']):
                category = 'stem'
            elif any(term in major_lower for term in ['business', 'finance', 'accounting', 'marketing']):
                category = 'business'
            elif any(term in major_lower for term in ['health', 'medical', 'nursing', 'pharmacy']):
                category = 'healthcare'
            elif any(term in major_lower for term in ['education', 'teaching']):
                category = 'education'
            elif any(term in major_lower for term in ['humanities', 'arts', 'social']):
                category = 'humanities'
            elif any(term in major_lower for term in ['trade', 'vocational', 'construction']):
                category = 'trades'

        # Get base earnings
        earnings = major_averages[category].copy()

        # Apply regional adjustment
        regional_multiplier = 1.0
        if institution_region:
            region_lower = institution_region.lower()
            for region, factor in regional_factors.items():
                if region in region_lower:
                    regional_multiplier = factor
                    break

        # Apply tuition-based adjustment (higher tuition often correlates with higher earnings)
        tuition_multiplier = 1.0
        if tuition_in_state and tuition_in_state > 0:
            if tuition_in_state > 40000:  # Very high tuition (private elite)
                tuition_multiplier = 1.15
            elif tuition_in_state > 25000:  # High tuition
                tuition_multiplier = 1.08
            elif tuition_in_state < 8000:  # Low tuition (public)
                tuition_multiplier = 0.95

        # Apply adjustments
        final_multiplier = regional_multiplier * tuition_multiplier
        for key in earnings:
            earnings[key] = int(earnings[key] * final_multiplier)

        return earnings

    def _get_national_average_trajectory(self, major_category: Optional[str]) -> List[int]:
        """
        Get national average earnings trajectory when all else fails
        """
        fallback = self._get_fallback_earnings(major_category, None, None)

        # Build 25-year trajectory using the fallback values
        trajectory = [0] * 25
        trajectory[0] = fallback['year_1']
        trajectory[2] = fallback['year_3']
        trajectory[4] = fallback['year_5']

        # Fill the rest using standard growth patterns
        for year in range(5, 25):
            if trajectory[year] == 0:
                if year <= 7:
                    growth_rate = 0.05
                elif year <= 12:
                    growth_rate = 0.035
                elif year <= 17:
                    growth_rate = 0.025
                else:
                    growth_rate = 0.015
                trajectory[year] = int(trajectory[year - 1] * (1 + growth_rate))

        return trajectory

    def _calculate_effective_after_tax_income(self, annual_earnings: int, tax_rate: float) -> int:
        """
        Calculate after-tax income using progressive tax brackets for realism
        """
        if annual_earnings <= 0:
            return 0

        # Simplified progressive tax calculation
        if annual_earnings <= 11000:  # Standard deduction + low bracket
            effective_rate = 0.02  # Very low effective rate
        elif annual_earnings <= 44725:
            effective_rate = 0.08
        elif annual_earnings <= 95375:
            effective_rate = 0.15
        elif annual_earnings <= 182100:
            effective_rate = 0.20
        elif annual_earnings <= 231250:
            effective_rate = 0.25
        else:
            effective_rate = 0.30

        # Blend user-provided tax rate with calculated effective rate
        blended_rate = (tax_rate + effective_rate) / 2

        return int(annual_earnings * (1 - blended_rate))

    def _calculate_payment_percentage(self, year: int, earnings: int, disposable_income: int) -> float:
        """
        Calculate appropriate debt payment percentage based on career stage and financial situation

        Considers:
        - Career stage (early vs established)
        - Earnings level
        - Disposable income ratio
        """
        # Base percentages by career stage
        if year == 1:
            base_percentage = 0.08  # Conservative early career
        elif year <= 3:
            base_percentage = 0.12  # Building career
        elif year <= 7:
            base_percentage = 0.15  # Established career
        else:
            base_percentage = 0.18  # Senior level

        # Adjust based on earnings level (higher earners can pay more)
        if earnings >= 150000:  # High earners
            base_percentage *= 1.2
        elif earnings >= 100000:  # Good earners
            base_percentage *= 1.1
        elif earnings <= 35000:  # Low earners
            base_percentage *= 0.8

        # Adjust based on disposable income ratio
        disposable_ratio = disposable_income / earnings if earnings > 0 else 0
        if disposable_ratio < 0.3:  # Tight budget
            base_percentage *= 0.9
        elif disposable_ratio > 0.7:  # Plenty of disposable income
            base_percentage *= 1.1

        # Ensure reasonable bounds
        return max(0.03, min(0.25, base_percentage))  # 3%-25% range
    
    def calculate_dti(
        self,
        total_debt: int,
        earnings_year_1: Optional[int]
    ) -> Optional[float]:
        """
        Calculate Debt-to-Income ratio for year 1
        
        DTI = Total Debt / Annual Income
        
        Args:
            total_debt: Total debt at graduation
            earnings_year_1: First year earnings
            
        Returns:
            DTI ratio or None if no earnings data
        """
        if not earnings_year_1 or earnings_year_1 <= 0:
            return None
        
        dti = total_debt / earnings_year_1
        
        return round(dti, 2)
    
    def calculate_comfort_index(
        self,
        earnings_year_1: Optional[int],
        total_debt: int,
        dti: Optional[float],
        graduation_rate: Optional[float]
    ) -> Optional[float]:
        """
        Calculate financial comfort index (0-100)
        
        Higher is better. Considers:
        - Earnings level
        - Debt burden
        - Graduation likelihood
        
        Args:
            earnings_year_1: First year earnings
            total_debt: Total debt at graduation
            dti: Debt-to-income ratio
            graduation_rate: Graduation rate (0-1)
            
        Returns:
            Comfort index (0-100) or None
        """
        if not earnings_year_1:
            return None
        
        # Earnings score (0-40 points)
        # $50K = 20 points, $100K+ = 40 points
        earnings_score = min(40, (earnings_year_1 / 100000) * 40)
        
        # Debt score (0-30 points, inverse)
        # DTI < 0.5 = 30 points, DTI > 2.0 = 0 points
        if dti is not None:
            if dti <= 0.5:
                debt_score = 30
            elif dti >= 2.0:
                debt_score = 0
            else:
                debt_score = 30 * (1 - (dti - 0.5) / 1.5)
        else:
            debt_score = 15  # Neutral if no debt data
        
        # Graduation rate score (0-30 points)
        if graduation_rate is not None:
            grad_score = graduation_rate * 30
        else:
            grad_score = 15  # Neutral if no data
        
        comfort_index = earnings_score + debt_score + grad_score
        
        return round(comfort_index, 1)
    
    def apply_regional_adjustment(
        self,
        salary: int,
        rpp_index: Optional[float]
    ) -> int:
        """
        Adjust salary for regional cost of living
        
        Args:
            salary: Nominal salary
            rpp_index: Regional Price Parity index (100 = national average)
            
        Returns:
            Adjusted salary
        """
        if rpp_index is None or rpp_index == 0:
            return salary
        
        # Convert to purchasing power equivalent
        adjusted = salary / (rpp_index / 100)
        
        return int(adjusted)
    
    def calculate_housing_cost(
        self,
        fmr_monthly: int,
        roommate_count: int
    ) -> int:
        """
        Calculate annual housing cost adjusted for roommates
        
        Args:
            fmr_monthly: Fair Market Rent monthly
            roommate_count: Number of roommates
            
        Returns:
            Annual housing cost
        """
        # Split rent among roommates + self
        monthly_share = fmr_monthly / (roommate_count + 1)
        annual_cost = int(monthly_share * 12)
        
        return annual_cost
    
    def get_default_values(self) -> Dict[str, Any]:
        """
        Get default assumption values
        
        Returns:
            Dictionary of default values
        """
        return {
            "program_years": self.DEFAULT_PROGRAM_YEARS,
            "food_monthly": self.DEFAULT_FOOD_MONTHLY,
            "transport_monthly": self.DEFAULT_TRANSPORT_MONTHLY,
            "books_annual": self.DEFAULT_BOOKS_ANNUAL,
            "misc_monthly": self.DEFAULT_MISC_MONTHLY,
            "utilities_monthly": self.DEFAULT_UTILITIES_MONTHLY
        }

