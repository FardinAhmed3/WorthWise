"""About page - Data sources, methodology, and KPI formulas"""

import streamlit as st
from src.data.constants import DATA_VERSIONS, DEFAULT_BASELINE_EARNINGS


def show_about_page():
    """Render the About page"""
    st.title("📚 About & Methodology")
    st.markdown("Learn about the data sources, calculations, and assumptions used in this tool.")
    
    # Data Sources
    st.header("Data Sources")
    
    st.markdown(f"""
    This tool integrates multiple authoritative data sources to provide accurate financial projections:
    
    ### 1. College Scorecard ({DATA_VERSIONS['college_scorecard']})
    **Source:** U.S. Department of Education  
    **URL:** https://collegescorecard.ed.gov/data/
    
    **Data Used:**
    - Institution details (name, location, control type)
    - Tuition and fees (in-state and out-of-state)
    - Graduation rates (4-year completion)
    - Program-level median earnings (1-year and 4-year post-graduation)
    - Median debt at graduation by program
    
    ### 2. HUD Small Area Fair Market Rents ({DATA_VERSIONS['hud_safmrs']})
    **Source:** U.S. Department of Housing and Urban Development  
    **URL:** https://www.huduser.gov/portal/datasets/fmr.html
    
    **Data Used:**
    - State-level median 1-bedroom and 2-bedroom rents
    - Aggregated from ZIP code-level Small Area Fair Market Rent (SAFMR) data
    - Includes data from FY2021 through FY2026 for comprehensive coverage
    - SAFMRS provide more granular, zip code-level rent estimates compared to traditional FMRs
    
    ### 3. BLS Consumer Price Index ({DATA_VERSIONS['bls_cpi']})
    **Source:** U.S. Bureau of Labor Statistics  
    **URL:** https://www.bls.gov/cpi/data.htm
    
    **Data Used:**
    - Annual CPI values for inflation adjustment
    - All items CPI-U (Consumer Price Index for All Urban Consumers)
    
    ### 4. ACS PUMS ({DATA_VERSIONS['acs_pums']})
    **Source:** U.S. Census Bureau  
    **URL:** https://www.census.gov/programs-surveys/acs/microdata.html
    
    **Data Used:**
    - State-level median earnings by education level
    - Used as fallback when program-specific earnings are unavailable
    """)
    
    st.divider()
    
    # Methodology
    st.header("Calculation Methodology")
    
    st.subheader("Key Performance Indicators (KPIs)")
    
    with st.expander("💰 Total Yearly Cost of Attendance"):
        st.markdown("""
        **Formula:**
        ```
        Total Cost = Tuition + Housing + Food + Transport + Books + Misc
        ```
        
        **Adjustments:**
        - **Roommate Discount:** 25% reduction in housing cost per roommate (max 75%)
        - **Living at Home:** 70% reduction in housing costs
        
        **Default Values:**
        - Food: $400/month ($4,800/year)
        - Transportation: $200/month ($2,400/year)
        - Books & Supplies: $1,200/year
        - Miscellaneous: $2,000/year
        """)
    
    with st.expander("🎓 Expected Debt at Graduation"):
        st.markdown("""
        **Formula:**
        ```
        Yearly Debt = max(0, Total Cost - Grants - Scholarships - Work Study - Family Contribution)
        Cumulative Debt = Yearly Debt × 4 years
        ```
        
        **Assumptions:**
        - 4-year degree completion
        - Constant aid amounts each year
        - Any shortfall is covered by loans
        """)
    
    with st.expander("💵 Earnings Projections"):
        st.markdown("""
        **Formula:**
        ```
        Year 1 = Median earnings from College Scorecard
        Year 3 = Year 1 × (1.03)²
        Year 5 = Year 1 × (1.03)⁴
        ```
        
        **Assumptions:**
        - 3% annual salary growth (conservative estimate)
        - Based on program-specific median earnings
        - Falls back to state median if program data unavailable
        """)
    
    with st.expander("📈 Return on Investment (ROI)"):
        st.markdown(f"""
        **Formula:**
        ```
        5-Year Cumulative Earnings = Average(Year 1, Year 5) × 5
        5-Year Baseline Earnings = ${DEFAULT_BASELINE_EARNINGS:,} × 5
        Net Benefit = 5-Year Cumulative - Baseline - Total Cost
        ROI = (Net Benefit / Total Cost) × 100
        ```
        
        **Assumptions:**
        - Baseline: ${DEFAULT_BASELINE_EARNINGS:,}/year (high school graduate)
        - 5-year time horizon for ROI calculation
        - Simplified linear earnings growth
        """)
    
    with st.expander("⏱️ Payback Period"):
        st.markdown("""
        **Formula:**
        ```
        Annual Payment = Year 1 Salary × 10%
        Payback Period = Total Debt / Annual Payment
        ```
        
        **Assumptions:**
        - 10% of gross income allocated to debt repayment
        - Simplified calculation (does not account for interest)
        - Capped at 50 years for display
        """)
    
    with st.expander("📊 Debt-to-Income (DTI) Ratio"):
        st.markdown("""
        **Formula:**
        ```
        Monthly Payment = Loan amortization formula
        Monthly Income = (Year 1 Salary × (1 - Tax Rate)) / 12
        DTI = (Monthly Payment / Monthly Income) × 100
        ```
        
        **Loan Payment Formula:**
        ```
        P × [r(1+r)ⁿ] / [(1+r)ⁿ - 1]
        where:
        P = Principal (total debt)
        r = Monthly interest rate
        n = Number of payments (120 for 10 years)
        ```
        
        **Assumptions:**
        - 10-year loan term
        - Standard amortization
        - Default APR: 5.5%
        - Default tax rate: 22%
        """)
    
    with st.expander("🎯 Financial Comfort Index"):
        st.markdown("""
        **Formula:**
        ```
        DTI Score = max(0, 100 - (DTI × 2))
        Graduation Score = Graduation Rate × 100
        ROI Score = max(0, min(100, (ROI + 100) / 2))
        
        Comfort Index = (DTI Score × 40%) + (Grad Score × 30%) + (ROI Score × 30%)
        ```
        
        **Weights:**
        - Debt-to-Income Ratio: 40% (lower is better)
        - Graduation Rate: 30% (higher is better)
        - Return on Investment: 30% (higher is better)
        
        **Interpretation:**
        - 70-100: Excellent financial outlook
        - 50-69: Good financial outlook
        - 30-49: Fair financial outlook
        - 0-29: Challenging financial outlook
        """)
    
    st.divider()
    
    # Limitations
    st.header("Limitations & Assumptions")
    
    st.markdown("""
    ### Data Limitations
    - **State-Level Aggregation:** Housing costs and earnings are aggregated at the state level, not county or metro area
    - **Historical Data:** College Scorecard earnings are from past cohorts and may not reflect current market conditions
    - **Missing Data:** Some programs may lack earnings or debt data due to privacy suppression or small sample sizes
    
    ### Calculation Simplifications
    - **Constant Aid:** Assumes financial aid remains constant across all 4 years
    - **No Interest During School:** Does not model interest accrual during enrollment
    - **Linear Growth:** Earnings growth is modeled as simple compound growth at 3% annually
    - **Simplified Payback:** Payback period calculation does not account for loan interest
    
    ### Out of Scope
    - Graduate and professional programs (Master's, PhD, JD, MD)
    - International institutions
    - Part-time or non-traditional enrollment patterns
    - Room and board variations beyond roommate count
    - State residency changes affecting tuition
    """)
    
    st.divider()
    
    # Fallback Logic
    st.header("Missing Data Handling")
    
    st.markdown("""
    When specific data points are unavailable, the tool uses the following fallback logic:
    
    | Data Point | Fallback Strategy |
    |------------|------------------|
    | Program Earnings | State median earnings |
    | State Housing Cost | National median ($12,000/year) |
    | Tuition (Public) | $10,000/year |
    | Tuition (Private) | $30,000/year |
    | Graduation Rate | 50% |
    | CPI Multiplier | 1.0 (no adjustment) |
    
    **Note:** Fallback values are conservative estimates and may not reflect actual costs or outcomes.
    """)
    
    st.divider()
    
    # Footer
    st.header("About This Tool")
    
    st.markdown("""
    **Version:** 1.0.0  
    **Last Updated:** 2024
    
    This tool is designed to help prospective students make informed decisions about college enrollment
    by providing transparent financial projections based on authoritative data sources.
    
    **Disclaimer:** This tool provides estimates based on historical data and assumptions. Actual costs,
    earnings, and outcomes may vary significantly. Users should conduct additional research and consult
    with financial advisors before making enrollment decisions.
    
    **Data Refresh:** All data is static and processed at deployment time. For the most current data,
    visit the source websites listed above.
    """)



