"""
Analytics Service
Query DuckDB for program data and compute KPIs
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.duckdb_client import DuckDBClient
from app.services.roi_calculator import ROICalculator
from app.schemas.compute import ComputeRequest, KPIResult
from app.utils.exceptions import DataNotFoundException, InsufficientDataException
from app.models import Institution, CIPCode


class AnalyticsService:
    """
    Service for querying analytical data and computing KPIs
    Bridges MySQL (reference data) and DuckDB (analytics)
    """
    
    def __init__(self, duckdb_client: DuckDBClient):
        self.duckdb = duckdb_client
        self.calculator = ROICalculator()
    
    def get_program_data(
        self,
        institution_id: int,
        cip_code: str,
        credential_level: int = 3
    ) -> Dict[str, Any]:
        """
        Get program-level data from DuckDB
        
        Returns earnings, debt, and other program metrics
        """
        try:
            # Query DuckDB for program data
            # NOTE: Dataset only has earnings_1yr, earnings_4yr, earnings_5yr
            # No earnings_2yr or earnings_3yr available
            sql = """
                SELECT 
                    institution_id,
                    cip_code,
                    credential_level,
                    earnings_1yr,
                    earnings_4yr,
                    earnings_5yr,
                    debt_median,
                    debt_mean,
                    earners_count,
                    awards_count
                FROM programs
                WHERE institution_id = ? AND cip_code = ? AND credential_level = ?
                LIMIT 1
            """
            
            result = self.duckdb.query_one(sql, (institution_id, cip_code, credential_level))
            
            if not result:
                raise DataNotFoundException(
                    f"Program not found: institution={institution_id}, cip={cip_code}"
                )
            
            # Convert to dictionary
            columns = ["institution_id", "cip_code", "credential_level",
                      "earn_1yr", "earn_4yr", "earn_5yr",
                      "debt_median", "debt_mean",
                      "earners_count", "awards_count"]
            
            data = dict(zip(columns, result))
            
            # Calculate earn_3yr by linear interpolation between earn_1yr and earn_4yr
            if data.get("earn_1yr") and data.get("earn_4yr"):
                data["earn_3yr"] = int(data["earn_1yr"] + (data["earn_4yr"] - data["earn_1yr"]) * (2/3))
            else:
                data["earn_3yr"] = None
            
            return data
            
        except Exception as e:
            # Fallback: return None values if DuckDB query fails
            return {
                "earn_1yr": None,
                "earn_3yr": None,
                "earn_5yr": None,
                "debt_median": None
            }
    
    def get_institution_data(
        self,
        db: Session,
        institution_id: int
    ) -> Dict[str, Any]:
        """
        Get institution data from MySQL
        
        Returns tuition, graduation rate, etc.
        """
        institution = db.query(Institution).filter(
            Institution.id == institution_id
        ).first()
        
        if not institution:
            raise DataNotFoundException(f"Institution {institution_id} not found")
        
        return {
            "id": institution.id,
            "name": institution.name,
            "state_code": institution.state_code,
            "zip": institution.zip,
            "ownership": institution.ownership,
            "tuition_in_state": institution.tuition_in_state,
            "tuition_out_state": institution.tuition_out_state,
            "avg_net_price_public": institution.avg_net_price_public,
            "avg_net_price_private": institution.avg_net_price_private
        }
    
    def get_housing_cost(
        self,
        zip_code: str,
        housing_type: str
    ) -> Optional[int]:
        """
        Get Fair Market Rent from DuckDB
        
        Returns monthly rent or None
        """
        try:
            # Map housing type to FMR column
            fmr_column_map = {
                "studio": "safmr_0br",
                "0BR": "safmr_0br",
                "1BR": "safmr_1br",
                "2BR": "safmr_2br",
                "3BR": "safmr_3br",
                "4BR": "safmr_4br"
            }
            
            column = fmr_column_map.get(housing_type, "safmr_1br")
            
            sql = f"""
                SELECT {column}
                FROM fmr_latest
                WHERE zip_code = ?
                LIMIT 1
            """
            
            result = self.duckdb.query_one(sql, (zip_code,))
            
            if result and result[0]:
                return int(result[0])
            
            return None
            
        except:
            return None
    
    def get_regional_rpp(
        self,
        region_id: int
    ) -> Optional[float]:
        """
        Get Regional Price Parity index from DuckDB
        
        Returns RPP index (100 = national average) or None
        """
        try:
            sql = """
                SELECT rpp_index
                FROM rpp_latest
                WHERE region_id = ?
                LIMIT 1
            """
            
            result = self.duckdb.query_one(sql, (region_id,))
            
            if result and result[0]:
                return float(result[0])
            
            return None
            
        except:
            return None
    
    def compute_kpis(
        self,
        db: Session,
        request: ComputeRequest
    ) -> tuple[KPIResult, Dict[str, Any], List[str]]:
        """
        Main computation method: calculate all KPIs for a scenario
        
        Returns:
            Tuple of (KPIResult, assumptions_dict, warnings_list)
        """
        warnings = []
        assumptions = self.calculator.get_default_values()
        
        # 1. Get institution data
        try:
            inst_data = self.get_institution_data(db, request.institution_id)
        except DataNotFoundException:
            raise
        
        # 2. Get program earnings/debt data
        program_data = self.get_program_data(
            request.institution_id,
            request.cip_code,
            request.credential_level
        )
        
        if not program_data.get("earn_1yr"):
            warnings.append("No earnings data available for this program - using estimates")
        
        # 3. Get housing cost
        if request.housing_type == "none":
            # No housing cost for students living at home with parents
            fmr_monthly = 0
            housing_annual = 0
            assumptions["rent_source"] = "none"
        elif request.rent_monthly:
            fmr_monthly = request.rent_monthly
            assumptions["rent_source"] = "user_provided"
            # Calculate housing cost (adjusted for roommates)
            housing_annual = self.calculator.calculate_housing_cost(
                fmr_monthly,
                request.roommate_count
            )
        else:
            # Use FMR data
            fmr_monthly = self.get_housing_cost(
                inst_data.get("zip", ""),
                request.housing_type
            )
            if not fmr_monthly:
                fmr_monthly = 1200  # Default fallback
                warnings.append(f"No FMR data for ZIP code - using default ${fmr_monthly}/month")
            assumptions["rent_source"] = "hud_fmr"
            
            # Calculate housing cost (adjusted for roommates)
            housing_annual = self.calculator.calculate_housing_cost(
                fmr_monthly,
                request.roommate_count
            )
        
        # 5. Get other costs (use user overrides or defaults)
        food_monthly = request.food_monthly if request.food_monthly is not None else assumptions["food_monthly"]
        transport_monthly = request.transport_monthly if request.transport_monthly is not None else assumptions["transport_monthly"]
        utilities_monthly = request.utilities_monthly if request.utilities_monthly is not None else assumptions["utilities_monthly"]
        misc_monthly = request.misc_monthly if request.misc_monthly is not None else assumptions["misc_monthly"]
        books_annual = request.books_annual if request.books_annual is not None else assumptions["books_annual"]
        
        # 6. Get tuition based on residency status and institution type
        ownership = inst_data.get("ownership", 1)
        tuition_in_state = inst_data.get("tuition_in_state")
        tuition_out_state = inst_data.get("tuition_out_state")
        avg_net_price_public = inst_data.get("avg_net_price_public")
        avg_net_price_private = inst_data.get("avg_net_price_private")
        
        # Determine tuition based on ownership and residency
        if ownership == 1:  # Public
            if request.is_instate and tuition_in_state:
                tuition_fees = tuition_in_state
            elif not request.is_instate and tuition_out_state:
                tuition_fees = tuition_out_state
            elif avg_net_price_public:
                tuition_fees = avg_net_price_public
                warnings.append("Using average net price (tuition data unavailable)")
            else:
                tuition_fees = 14000  # Fallback
                warnings.append("Using estimated tuition (data unavailable)")
        elif ownership == 2:  # Private nonprofit
            if avg_net_price_private:
                tuition_fees = avg_net_price_private
            elif tuition_in_state:  # Private schools often use same tuition
                tuition_fees = tuition_in_state
            else:
                tuition_fees = 35000  # Fallback
                warnings.append("Using estimated tuition (data unavailable)")
        else:  # Private for-profit
            if tuition_in_state:
                tuition_fees = tuition_in_state
            elif avg_net_price_private:
                tuition_fees = avg_net_price_private
            else:
                tuition_fees = 25000  # Fallback
                warnings.append("Using estimated tuition (data unavailable)")
        
        # 7. Calculate total cost
        true_yearly_cost, housing_annual, other_expenses = self.calculator.calculate_total_cost(
            tuition_fees,
            housing_annual,
            food_monthly,
            transport_monthly,
            utilities_monthly,
            misc_monthly,
            books_annual
        )
        
        # 8. Calculate debt
        program_years = assumptions["program_years"]
        expected_debt = self.calculator.calculate_debt(
            true_yearly_cost,
            request.aid_annual,
            request.cash_annual,
            program_years,
            request.loan_apr
        )
        
        # 9. Get earnings projections (data has 1yr, 4yr, 5yr; 3yr is interpolated)
        earnings_year_1 = program_data.get("earn_1yr")
        earnings_year_3 = program_data.get("earn_3yr")  # Interpolated from 1yr and 4yr
        earnings_year_5 = program_data.get("earn_5yr")
        
        # Apply regional adjustment if provided
        if request.postgrad_region_id:
            rpp = self.get_regional_rpp(request.postgrad_region_id)
            if rpp and earnings_year_1:
                earnings_year_1 = self.calculator.apply_regional_adjustment(
                    earnings_year_1, rpp
                )
            if rpp and earnings_year_3:
                earnings_year_3 = self.calculator.apply_regional_adjustment(
                    earnings_year_3, rpp
                )
        
        # 10. Calculate KPIs
        total_investment = (true_yearly_cost * program_years) - (request.aid_annual * program_years)
        
        # Calculate ROI with all available earnings data
        roi = self.calculator.calculate_roi(
            total_investment,
            earnings_year_1=earnings_year_1,
            earnings_year_3=earnings_year_3,
            earnings_year_5=earnings_year_5
        )
        
        # Get major category for earnings fallback
        major_category = None
        if request.cip_code:
            # Extract major category from CIP code (first 2 digits indicate broad field)
            try:
                cip_prefix = request.cip_code.split('.')[0]
                cip_category_map = {
                    '11': 'stem', '14': 'stem', '15': 'stem', '26': 'stem', '27': 'stem', '40': 'stem', '41': 'stem',
                    '52': 'business', '13': 'education', '51': 'healthcare',
                    '23': 'humanities', '24': 'humanities', '25': 'humanities', '30': 'humanities', '31': 'humanities',
                    '46': 'trades', '47': 'trades', '48': 'trades', '49': 'trades'
                }
                major_category = cip_category_map.get(cip_prefix, 'business')
            except:
                major_category = 'business'

        # Calculate payback period using robust, production-ready approach
        payback_years = self.calculator.calculate_payback_period(
            total_debt=expected_debt,
            earnings_year_1=earnings_year_1,
            earnings_year_3=earnings_year_3,
            earnings_year_5=earnings_year_5,
            effective_tax_rate=request.effective_tax_rate,
            loan_apr=request.loan_apr,
            living_expenses_annual=45000,  # Configurable default
            tuition_in_state=inst_data.get("tuition_in_state"),
            major_category=major_category,
            institution_region=inst_data.get("state_code")
        )
        
        dti_year_1 = self.calculator.calculate_dti(expected_debt, earnings_year_1)
        
        # Placeholder graduation rate
        graduation_rate = 0.75  # Would come from College Scorecard
        
        comfort_index = self.calculator.calculate_comfort_index(
            earnings_year_1,
            expected_debt,
            dti_year_1,
            graduation_rate
        )
        
        # 11. Build KPI result
        kpis = KPIResult(
            true_yearly_cost=true_yearly_cost,
            tuition_fees=tuition_fees,
            housing_annual=housing_annual,
            other_expenses=other_expenses,
            expected_debt_at_grad=expected_debt,
            earnings_year_1=earnings_year_1,
            earnings_year_3=earnings_year_3,
            earnings_year_5=earnings_year_5,
            roi=roi,
            payback_years=payback_years,
            dti_year_1=dti_year_1,
            graduation_rate=graduation_rate,
            comfort_index=comfort_index
        )
        
        return kpis, assumptions, warnings

