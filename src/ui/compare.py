"""Compare page - Side-by-side comparison of 2 programs"""

import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Dict, Any, Tuple

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
    DEFAULT_BASELINE_EARNINGS, HOUSING_MULTIPLIERS,
    ROOMMATE_REDUCTION_RATE, MAX_ROOMMATE_DISCOUNT, MIN_LOAN_APR, MAX_LOAN_APR,
    MIN_TAX_RATE, MAX_TAX_RATE, LOAN_APR_STEP, TAX_RATE_STEP,
    DEFAULT_PAYMENT_RATE, DEFAULT_GRADUATION_RATE
)


def calculate_program_metrics(
    inst_details: Dict,
    prog_details: Dict,
    data_loader,
    shared_params: Dict
) -> Dict[str, Any]:
    """Calculate all metrics for a program"""
    
    # Get tuition
    if inst_details['control_type'] == 1:  # Public
        tuition = inst_details.get('tuition_in_state', 10000) or 10000
    else:
        tuition = inst_details.get('tuition_out_state', 30000) or 30000
    
    # Get housing cost
    base_housing = data_loader.get_state_housing_cost(inst_details['state'])
    if shared_params['housing_type'] == 'Living at Home':
        base_housing *= HOUSING_MULTIPLIERS['at_home']
    
    # Calculate costs
    annual_housing = base_housing
    annual_food = shared_params['food_monthly'] * 12
    annual_transport = shared_params['transport_monthly'] * 12
    annual_books = DEFAULT_BOOKS_YEARLY
    annual_misc = DEFAULT_MISC_YEARLY
    
    total_annual_cost = calculate_total_cost_of_attendance(
        tuition=tuition,
        housing=annual_housing,
        food=annual_food,
        transport=annual_transport,
        books=annual_books,
        misc=annual_misc,
        roommate_count=shared_params['roommate_count']
    )
    
    # Calculate debt
    cumulative_debt = calculate_cumulative_debt(
        yearly_cost=total_annual_cost,
        grants=shared_params['grants'],
        scholarships=shared_params['scholarships'],
        work_study=shared_params['work_study'],
        family_contribution=shared_params['family_contribution'],
        years=4
    )
    
    # Get earnings
    year1_earnings = prog_details.get('median_earnings_1yr')
    if pd.isna(year1_earnings) or year1_earnings is None:
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
        annual_rate=shared_params['loan_apr'],
        years=10
    )
    
    monthly_income = calculate_monthly_budget(year1, shared_params['tax_rate'])
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
    
    return {
        'institution_name': inst_details['institution_name'],
        'program_name': prog_details['program_name'],
        'state': inst_details['state'],
        'total_annual_cost': total_annual_cost,
        'cumulative_debt': cumulative_debt,
        'year1': year1,
        'year3': year3,
        'year5': year5,
        'roi': roi,
        'payback': payback,
        'dti': dti,
        'grad_rate': grad_rate,
        'comfort': comfort,
        'tuition': tuition,
        'housing': annual_housing * (1 - min(shared_params['roommate_count'] * ROOMMATE_REDUCTION_RATE, MAX_ROOMMATE_DISCOUNT)),
        'food': annual_food,
        'transport': annual_transport,
        'books': annual_books,
        'misc': annual_misc
    }


def show_compare_page():
    """Render the Compare page"""
    st.title("⚖️ Compare Programs")
    st.markdown("**Compare two college programs side-by-side with detailed financial analysis and visual comparisons.**")
    
    # Add a status indicator
    with st.container():
        st.info("💡 **Tip**: Select two different programs to compare their financial outcomes, costs, and projected earnings.")
    
    # Get data loader from session state
    data_loader = st.session_state.data_loader
    
    # Shared parameters in sidebar
    with st.sidebar:
        st.header("Shared Parameters")
        
        housing_type = st.radio(
            "Housing Type",
            options=['On-Campus', 'Off-Campus', 'Living at Home'],
            index=0
        )
        
        roommate_count = st.slider(
            "Number of Roommates",
            min_value=0,
            max_value=3,
            value=0
        )
        
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
        
        grants = st.number_input(
            "Annual Grants",
            min_value=0,
            value=0,
            step=500
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
    
    shared_params = {
        'housing_type': housing_type,
        'roommate_count': roommate_count,
        'food_monthly': food_monthly,
        'transport_monthly': transport_monthly,
        'grants': grants,
        'scholarships': scholarships,
        'work_study': work_study,
        'family_contribution': family_contribution,
        'loan_apr': loan_apr,
        'tax_rate': tax_rate
    }
    
    # Program selection
    col1, col2 = st.columns(2)
    
    institutions = data_loader.get_institutions()
    
    if len(institutions) == 0:
        st.error("No institutions found. Please run the ETL pipeline first.")
        return
    
    # Create institution options
    inst_options = {}
    for _, row in institutions.iterrows():
        display_name = f"{row['institution_name']} ({row['state']})"
        inst_options[display_name] = row['unit_id']
    
    # Program 1 selection
    with col1:
        st.subheader("Program 1")
        
        selected_inst1_name = st.selectbox(
            "Institution",
            options=list(inst_options.keys()),
            key='inst1'
        )
        
        unit_id1 = inst_options[selected_inst1_name]
        inst1_details = data_loader.get_institution_details(unit_id1)
        
        programs1 = data_loader.get_programs(unit_id1)
        
        if len(programs1) > 0:
            prog1_options = {row['program_name']: row['cip_code'] for _, row in programs1.iterrows()}
            
            selected_prog1_name = st.selectbox(
                "Major/Program",
                options=list(prog1_options.keys()),
                key='prog1'
            )
            
            cip1 = prog1_options[selected_prog1_name]
            prog1_details = data_loader.get_program_details(unit_id1, cip1)
        else:
            st.warning("No programs available")
            return
    
    # Program 2 selection
    with col2:
        st.subheader("Program 2")
        
        selected_inst2_name = st.selectbox(
            "Institution",
            options=list(inst_options.keys()),
            key='inst2'
        )
        
        unit_id2 = inst_options[selected_inst2_name]
        inst2_details = data_loader.get_institution_details(unit_id2)
        
        programs2 = data_loader.get_programs(unit_id2)
        
        if len(programs2) > 0:
            prog2_options = {row['program_name']: row['cip_code'] for _, row in programs2.iterrows()}
            
            selected_prog2_name = st.selectbox(
                "Major/Program",
                options=list(prog2_options.keys()),
                key='prog2'
            )
            
            cip2 = prog2_options[selected_prog2_name]
            prog2_details = data_loader.get_program_details(unit_id2, cip2)
        else:
            st.warning("No programs available")
            return
    
    st.divider()
    
    # Calculate metrics for both programs
    metrics1 = calculate_program_metrics(inst1_details, prog1_details, data_loader, shared_params)
    metrics2 = calculate_program_metrics(inst2_details, prog2_details, data_loader, shared_params)
    
    # Comparison table with enhanced styling
    st.subheader("📊 Key Metrics Comparison")
    
    comparison_df = pd.DataFrame({
        '📋 Metric': [
            '🏛️ Institution',
            '🎓 Program',
            '🗺️ State',
            '💰 Total Yearly Cost',
            '💳 Expected Debt',
            '💵 Year 1 Salary',
            '💵 Year 5 Salary',
            '📈 ROI (%)',
            '⏱️ Payback Period',
            '📊 DTI Ratio (%)',
            '🎓 Graduation Rate (%)',
            '🎯 Comfort Index'
        ],
        f'📌 {metrics1["institution_name"][:30]}...': [
            metrics1['institution_name'],
            metrics1['program_name'],
            metrics1['state'],
            format_currency(metrics1['total_annual_cost']),
            format_currency(metrics1['cumulative_debt']),
            format_currency(metrics1['year1']),
            format_currency(metrics1['year5']),
            format_percentage(metrics1['roi']),
            format_years(metrics1['payback']),
            format_percentage(metrics1['dti']),
            format_percentage(metrics1['grad_rate'] * 100),
            f"{metrics1['comfort']:.0f}/100"
        ],
        f'📌 {metrics2["institution_name"][:30]}...': [
            metrics2['institution_name'],
            metrics2['program_name'],
            metrics2['state'],
            format_currency(metrics2['total_annual_cost']),
            format_currency(metrics2['cumulative_debt']),
            format_currency(metrics2['year1']),
            format_currency(metrics2['year5']),
            format_percentage(metrics2['roi']),
            format_years(metrics2['payback']),
            format_percentage(metrics2['dti']),
            format_percentage(metrics2['grad_rate'] * 100),
            f"{metrics2['comfort']:.0f}/100"
        ]
    })
    
    # Style the dataframe
    st.dataframe(
        comparison_df, 
        width='stretch', 
        hide_index=True,
        column_config={
            "📋 Metric": st.column_config.TextColumn(
                "Metric",
                help="Financial and academic metrics for comparison",
                width="medium"
            ),
            f'📌 {metrics1["institution_name"][:30]}...': st.column_config.TextColumn(
                "Program 1",
                help="First program metrics",
                width="medium"
            ),
            f'📌 {metrics2["institution_name"][:30]}...': st.column_config.TextColumn(
                "Program 2", 
                help="Second program metrics",
                width="medium"
            )
        }
    )
    
    st.divider()
    
    # Visualizations
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Cost Comparison")
        
        # Grouped bar chart for costs
        cost_comparison = pd.DataFrame({
            'Category': ['Tuition', 'Housing', 'Food', 'Transport', 'Books', 'Misc'] * 2,
            'Amount': [
                metrics1['tuition'], metrics1['housing'], metrics1['food'],
                metrics1['transport'], metrics1['books'], metrics1['misc'],
                metrics2['tuition'], metrics2['housing'], metrics2['food'],
                metrics2['transport'], metrics2['books'], metrics2['misc']
            ],
            'Program': ['Program 1'] * 6 + ['Program 2'] * 6
        })
        
        fig_cost = px.bar(
            cost_comparison,
            x='Category',
            y='Amount',
            color='Program',
            barmode='group',
            title='Annual Cost Components',
            labels={'Amount': 'Annual Cost ($)'}
        )
        st.plotly_chart(fig_cost, width='stretch', config={'displayModeBar': False})
    
    with col_right:
        st.subheader("Earnings Comparison")
        
        # Line chart for earnings
        earnings_comparison = pd.DataFrame({
            'Year': ['Year 1', 'Year 3', 'Year 5'] * 2,
            'Earnings': [
                metrics1['year1'], metrics1['year3'], metrics1['year5'],
                metrics2['year1'], metrics2['year3'], metrics2['year5']
            ],
            'Program': ['Program 1'] * 3 + ['Program 2'] * 3
        })
        
        fig_earnings = px.line(
            earnings_comparison,
            x='Year',
            y='Earnings',
            color='Program',
            markers=True,
            title='Projected Earnings Growth',
            labels={'Earnings': 'Annual Salary ($)'}
        )
        st.plotly_chart(fig_earnings, width='stretch', config={'displayModeBar': False})
    
    # Export comparison
    if st.button("📥 Export Comparison to CSV"):
        csv = comparison_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="college_roi_comparison.csv",
            mime="text/csv"
        )

