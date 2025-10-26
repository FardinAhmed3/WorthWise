"""Planner page - Single program ROI analysis"""

import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Dict, Any

from src.core.calculator import (
    calculate_total_cost_of_attendance,
    calculate_cumulative_debt,
    calculate_loan_payment,
    calculate_earnings_projection,
    calculate_roi,
    calculate_payback_period,
    calculate_dti_ratio,
    calculate_comfort_index,
    calculate_monthly_budget,
    format_currency,
    format_percentage,
    format_years
)
from src.data.constants import (
    DEFAULT_FOOD_MONTHLY, DEFAULT_UTILITIES_MONTHLY,
    DEFAULT_TRANSPORT_MONTHLY, DEFAULT_BOOKS_YEARLY,
    DEFAULT_MISC_YEARLY, DEFAULT_LOAN_APR, DEFAULT_TAX_RATE,
    DEFAULT_BASELINE_EARNINGS, CONTROL_TYPES, HOUSING_MULTIPLIERS,
    ROOMMATE_REDUCTION_RATE, MAX_ROOMMATE_DISCOUNT, MIN_LOAN_APR, MAX_LOAN_APR,
    MIN_TAX_RATE, MAX_TAX_RATE, LOAN_APR_STEP, TAX_RATE_STEP,
    DEFAULT_PAYMENT_RATE, DEFAULT_GRADUATION_RATE
)


def show_planner_page():
    """Render the Planner page"""
    st.title("🎓 College ROI Planner")
    st.markdown("**Analyze the financial outcomes of your college program choice with real data and comprehensive metrics.**")
    
    # Add a status indicator
    with st.container():
        st.info("💡 **Tip**: Use the sidebar to select your institution and program, then adjust financial parameters to see how they affect your ROI.")
    
    # Get data loader from session state
    data_loader = st.session_state.data_loader
    
    # Sidebar controls
    with st.sidebar:
        st.header("Program Selection")
        
        # State filter
        states = data_loader.get_states()
        selected_state = st.selectbox(
            "Filter by State",
            options=['All'] + states,
            index=0
        )
        
        # Institution selection
        if selected_state == 'All':
            institutions = data_loader.get_institutions()
        else:
            institutions = data_loader.get_institutions(selected_state)
        
        if len(institutions) == 0:
            st.error("No institutions found. Please run the ETL pipeline first.")
            return
        
        # Create institution display names
        inst_options = {}
        for _, row in institutions.iterrows():
            display_name = f"{row['institution_name']} ({row['city']}, {row['state']})"
            inst_options[display_name] = row['unit_id']
        
        selected_inst_name = st.selectbox(
            "Select Institution",
            options=list(inst_options.keys())
        )
        
        selected_unit_id = inst_options[selected_inst_name]
        
        # Get institution details
        inst_details = data_loader.get_institution_details(selected_unit_id)
        
        # Program selection
        programs = data_loader.get_programs(selected_unit_id)
        
        if len(programs) == 0:
            st.warning("No program data available for this institution.")
            return
        
        # Create program display names
        prog_options = {}
        for _, row in programs.iterrows():
            prog_options[row['program_name']] = row['cip_code']
        
        selected_prog_name = st.selectbox(
            "Select Major/Program",
            options=list(prog_options.keys())
        )
        
        selected_cip_code = prog_options[selected_prog_name]
        
        # Get program details
        prog_details = data_loader.get_program_details(selected_unit_id, selected_cip_code)
        
        st.divider()
        
        # Housing and living expenses
        st.header("Housing & Living")
        
        housing_type = st.radio(
            "Housing Type",
            options=['On-Campus', 'Off-Campus', 'Living at Home'],
            index=0
        )
        
        roommate_count = st.slider(
            "Number of Roommates",
            min_value=0,
            max_value=3,
            value=0,
            help="Reduces housing costs by 25% per roommate"
        )
        
        # Get base housing cost
        base_housing = data_loader.get_state_housing_cost(inst_details['state'])
        if housing_type == 'Living at Home':
            base_housing *= HOUSING_MULTIPLIERS['at_home']
        
        food_monthly = st.number_input(
            "Monthly Food Budget",
            min_value=0,
            value=DEFAULT_FOOD_MONTHLY,
            step=50
        )
        
        transport_monthly = st.number_input(
            "Monthly Transportation",
            min_value=0,
            value=DEFAULT_TRANSPORT_MONTHLY,
            step=25
        )
        
        st.divider()
        
        # Financial aid
        st.header("Financial Aid")
        
        grants = st.number_input(
            "Annual Grants",
            min_value=0,
            value=0,
            step=500,
            help="Non-repayable aid"
        )
        
        scholarships = st.number_input(
            "Annual Scholarships",
            min_value=0,
            value=0,
            step=500
        )
        
        work_study = st.number_input(
            "Annual Work-Study",
            min_value=0,
            value=0,
            step=500
        )
        
        family_contribution = st.number_input(
            "Annual Family Contribution",
            min_value=0,
            value=0,
            step=1000
        )
        
        st.divider()
        
        # Loan parameters
        st.header("Loan Parameters")
        
        loan_apr = st.slider(
            "Loan Interest Rate (APR)",
            min_value=MIN_LOAN_APR,
            max_value=MAX_LOAN_APR,
            value=DEFAULT_LOAN_APR,
            step=LOAN_APR_STEP,
            format="%.1f%%"
        ) 
        
        tax_rate = st.slider(
            "Effective Tax Rate",
            min_value=MIN_TAX_RATE,
            max_value=MAX_TAX_RATE,
            value=DEFAULT_TAX_RATE,
            step=TAX_RATE_STEP,
            format="%.0f%%"
        )
        
        if st.button("Reset to Defaults"):
            st.rerun()
    
    # Main content area
    # Only calculate metrics if we have valid selections
    if selected_inst_name and selected_prog_name and inst_details and prog_details:
        # Calculate all metrics
        
        # Get tuition
        if inst_details['control_type'] == 1:  # Public
            tuition = inst_details.get('tuition_in_state', 10000) or 10000
        else:
            tuition = inst_details.get('tuition_out_state', 30000) or 30000
    
        # Calculate costs
        annual_housing = base_housing
        annual_food = food_monthly * 12
        annual_transport = transport_monthly * 12
        annual_books = DEFAULT_BOOKS_YEARLY
        annual_misc = DEFAULT_MISC_YEARLY
    
        total_annual_cost = calculate_total_cost_of_attendance(
            tuition=tuition,
            housing=annual_housing,
            food=annual_food,
            transport=annual_transport,
            books=annual_books,
            misc=annual_misc,
            roommate_count=roommate_count
        )
    
        # Calculate debt
        cumulative_debt = calculate_cumulative_debt(
            yearly_cost=total_annual_cost,
            grants=grants,
            scholarships=scholarships,
            work_study=work_study,
            family_contribution=family_contribution,
            years=4
        )
    
        # Get earnings
        year1_earnings = prog_details.get('median_earnings_1yr')
        if pd.isna(year1_earnings) or year1_earnings is None:
            # Fallback to state median
            year1_earnings = data_loader.get_state_earnings(inst_details['state'])
        
        year1, year3, year5 = calculate_earnings_projection(year1_earnings)
    
        # Calculate ROI
        roi = calculate_roi(
            total_cost=total_annual_cost * 4,
            year5_earnings=year5,
            baseline_earnings=DEFAULT_BASELINE_EARNINGS
        )
    
        # Calculate loan payment and DTI
        monthly_payment = calculate_loan_payment(
            principal=cumulative_debt,
            annual_rate=loan_apr,
            years=10
        )
        
        monthly_income = calculate_monthly_budget(year1, tax_rate)
        dti = calculate_dti_ratio(monthly_payment, monthly_income)
        
        # Calculate payback period
        payback = calculate_payback_period(
            total_debt=cumulative_debt,
            annual_salary=year1,
            payment_rate=DEFAULT_PAYMENT_RATE
        )
        
        # Get graduation rate
        grad_rate = inst_details.get('graduation_rate', DEFAULT_GRADUATION_RATE) or DEFAULT_GRADUATION_RATE
        
        # Calculate comfort index
        comfort = calculate_comfort_index(dti, grad_rate, roi)
    
        # Display KPI cards with enhanced styling
        st.subheader("📊 Financial Analysis")
    
        # First row - Primary metrics
        col1, col2, col3, col4 = st.columns(4)
    
        with col1:
            st.metric(
                "💰 Total Yearly Cost",
                format_currency(total_annual_cost),
                help="Tuition + Housing + Food + Transport + Books + Misc"
            )
    
        with col2:
            st.metric(
                "💳 Expected Debt",
                format_currency(cumulative_debt),
                help="Total debt at graduation (4 years)"
            )
    
        with col3:
            st.metric(
                "💵 Year 1 Salary",
                format_currency(year1),
                help="Median earnings 1 year after graduation"
            )
        
        with col4:
            # Color code ROI
            if roi >= 100:
                delta_color = "normal"
                delta_value = "Excellent"
            elif roi >= 50:
                delta_color = "off"
                delta_value = "Good"
            else:
                delta_color = "inverse"
                delta_value = "Poor"
            
            st.metric(
                "📈 ROI",
                format_percentage(roi),
                delta=delta_value,
                help="Return on investment over 5 years"
            )
    
        # Second row - Secondary metrics
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            # Color code payback period
            if payback <= 5:
                delta_color = "normal"
                delta_value = "Fast"
            elif payback <= 10:
                delta_color = "off"
                delta_value = "Moderate"
            else:
                delta_color = "inverse"
                delta_value = "Slow"
            
            st.metric(
                "⏱️ Payback Period",
                format_years(payback),
                delta=delta_value,
                help="Years to pay off debt at 10% of income"
            )
    
        with col6:
            # Color code DTI ratio
            if dti <= 20:
                delta_color = "normal"
                delta_value = "Low"
            elif dti <= 35:
                delta_color = "off"
                delta_value = "Moderate"
            else:
                delta_color = "inverse"
                delta_value = "High"
            
            st.metric(
                "📊 DTI Ratio",
                format_percentage(dti),
                delta=delta_value,
                help="Debt-to-income ratio (monthly payment / monthly income)"
            )
    
        with col7:
            # Color code graduation rate
            if grad_rate >= 0.8:
                delta_color = "normal"
                delta_value = "High"
            elif grad_rate >= 0.6:
                delta_color = "off"
                delta_value = "Moderate"
            else:
                delta_color = "inverse"
                delta_value = "Low"
            
            st.metric(
                "🎓 Graduation Rate",
                format_percentage(grad_rate * 100),
                delta=delta_value,
                help="4-year graduation rate"
            )
    
        with col8:
            # Color code comfort index
            if comfort >= 70:
                delta_color = "normal"
                delta_value = "Excellent"
            elif comfort >= 50:
                delta_color = "off"
                delta_value = "Good"
            else:
                delta_color = "inverse"
                delta_value = "Poor"
            
            st.metric(
                "🎯 Comfort Index",
                f"{comfort:.0f}/100",
                delta=delta_value,
                help="Financial comfort score (0-100)"
            )
    
        st.divider()
        
        # Visualizations with enhanced styling
        st.subheader("📈 Visual Analysis")
        
        col_left, col_right = st.columns(2)
    
        with col_left:
            st.markdown("#### 💰 Cost Breakdown")
            
            # Cost breakdown bar chart with enhanced styling
            cost_data = pd.DataFrame({
                'Category': ['Tuition', 'Housing', 'Food', 'Transport', 'Books', 'Misc'],
                'Amount': [
                    tuition,
                    annual_housing * (1 - min(roommate_count * ROOMMATE_REDUCTION_RATE, MAX_ROOMMATE_DISCOUNT)),
                    annual_food,
                    annual_transport,
                    annual_books,
                    annual_misc
                ]
            })
        
            # Color palette for cost categories
            colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']
            
            fig_cost = px.bar(
                cost_data,
                x='Category',
                y='Amount',
                title='Annual Cost Components',
                labels={'Amount': 'Annual Cost ($)', 'Category': 'Cost Category'},
                color='Category',
                color_discrete_sequence=colors
            )
            
            fig_cost.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12),
                title=dict(x=0.5, font=dict(size=16))
            )
            
            fig_cost.update_traces(
                marker=dict(line=dict(width=0, color='white'))
            )
            
            st.plotly_chart(fig_cost, width='stretch', config={'displayModeBar': False})
    
        with col_right:
            st.markdown("#### 💵 Earnings Progression")
            
            # Earnings line chart with enhanced styling
            earnings_data = pd.DataFrame({
                'Year': ['Year 1', 'Year 3', 'Year 5'],
                'Earnings': [year1, year3, year5]
            })
            
            fig_earnings = px.line(
                earnings_data,
                x='Year',
                y='Earnings',
                title='Projected Earnings Growth',
                markers=True,
                labels={'Earnings': 'Annual Salary ($)', 'Year': 'Years Post-Graduation'}
            )
            
            fig_earnings.update_traces(
                line=dict(color='#667eea', width=4),
                marker=dict(size=12, color='#764ba2', line=dict(width=2, color='white'))
            )
            
            fig_earnings.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12),
                title=dict(x=0.5, font=dict(size=16)),
                xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            )
            
            st.plotly_chart(fig_earnings, width='stretch', config={'displayModeBar': False})
    
        # Assumptions panel
        with st.expander("📊 Assumptions & Data Sources"):
            st.markdown(f"""
        **Institution:** {inst_details['institution_name']}  
        **Program:** {prog_details['program_name']}  
        **Control Type:** {CONTROL_TYPES.get(inst_details['control_type'], 'Unknown')}
        
        **Cost Assumptions:**
        - Tuition: {format_currency(tuition)} per year
        - Housing: {format_currency(annual_housing)} per year (state median)
        - Roommate Adjustment: {roommate_count} roommate(s) = {roommate_count * 25}% discount
        - Books & Supplies: {format_currency(annual_books)} per year
        - Miscellaneous: {format_currency(annual_misc)} per year
        
        **Earnings Assumptions:**
        - Growth Rate: 3% annually
        - Baseline (no degree): {format_currency(DEFAULT_BASELINE_EARNINGS)}
        - Tax Rate: {format_percentage(tax_rate * 100)}
        
        **Loan Assumptions:**
        - Interest Rate: {format_percentage(loan_apr * 100)}
        - Term: 10 years
        - Monthly Payment: {format_currency(monthly_payment)}
        
        **Data Sources:**
        - College Scorecard (Most Recent Cohorts)
        - HUD Small Area Fair Market Rents (FY2021-FY2026)
        - BLS Consumer Price Index
        """)
        
        # Export to CSV
        if st.button("📥 Export Results to CSV"):
            export_data = pd.DataFrame({
                'Metric': [
                    'Institution',
                    'Program',
                    'Total Yearly Cost',
                    'Expected Debt at Graduation',
                    'Year 1 Salary',
                    'Year 3 Salary',
                    'Year 5 Salary',
                    'ROI (%)',
                    'Payback Period (years)',
                    'DTI Ratio (%)',
                    'Graduation Rate (%)',
                    'Comfort Index'
                ],
                'Value': [
                    inst_details['institution_name'],
                    prog_details['program_name'],
                    total_annual_cost,
                    cumulative_debt,
                    year1,
                    year3,
                    year5,
                    roi,
                    payback,
                    dti,
                    grad_rate * 100,
                    comfort
                ]
            })
            
            csv = export_data.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="college_roi_analysis.csv",
                mime="text/csv"
            )
    else:
        st.warning("Please select an institution and program to see the financial analysis.")

