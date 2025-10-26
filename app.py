"""
College ROI Planner - Main Streamlit Application
MVP Version 1.0.0
"""

import streamlit as st
from pathlib import Path

# Import UI components
from src.ui.planner import show_planner_page
from src.ui.compare import show_compare_page
from src.ui.about import show_about_page
from src.data.data_loader import DataLoader


# Page configuration
st.set_page_config(
    page_title="College ROI Planner",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for production-grade styling
st.markdown("""
<style>
    /* Main container styling */
    .main > div {
        padding-top: 1rem;
    }
    
    /* Streamlit metric cards styling */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #167ee3 0%, #764ba1 100%) !important;
        border: 1px solid #e1e5e9 !important;
        padding: 1.5rem !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        transition: transform 0.2s ease-in-out !important;
        margin-bottom: 1rem !important;
    }
    
    /* Alternative metric styling for different Streamlit versions */
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: 1px solid #e1e5e9 !important;
        padding: 1.5rem !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        transition: transform 0.2s ease-in-out !important;
        margin-bottom: 1rem !important;
    }
    
    /* Force override any white backgrounds */
    div[data-testid="metric-container"],
    .metric-container,
    .stMetric > div,
    .stMetric,
    [data-testid="metric-container"] > div,
    .element-container .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        background-color: transparent !important;
    }
    
    /* Additional metric styling for comprehensive coverage */
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: 1px solid #e1e5e9 !important;
        padding: 1.5rem !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        transition: transform 0.2s ease-in-out !important;
        margin-bottom: 1rem !important;
    }
    
    /* Override any inline styles that might be setting white backgrounds */
    div[style*="background-color: white"],
    div[style*="background: white"],
    .stMetric[style*="background-color: white"],
    .stMetric[style*="background: white"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        background-color: transparent !important;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
    }
    
    /* Metric value styling */
    div[data-testid="metric-container"] > div {
        color: white !important;
    }
    
    div[data-testid="metric-container"] label {
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 600;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    div[data-testid="metric-container"] div[data-testid="metric-value"] {
        color: white !important;
        font-size: 2rem;
        font-weight: 700;
        margin-top: 0.5rem;
    }
    
    div[data-testid="metric-container"] div[data-testid="metric-delta"] {
        color: rgba(255, 255, 255, 0.8) !important;
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }
    
    /* Header styling */
    h1 {
        color: #1f77b4;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        color: #2ca02c;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    
    h3 {
        color: #ff7f0e;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: white;
        border-radius: 8px;
        border: 2px solid #e1e5e9;
        transition: border-color 0.3s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #667eea;
    }
    
    /* Number input styling */
    .stNumberInput > div > div > input {
        background-color: white;
        border-radius: 8px;
        border: 2px solid #e1e5e9;
        transition: border-color 0.3s ease;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Slider styling */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Radio button styling */
    .stRadio > div {
        background-color: white;
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid #e1e5e9;
    }
    
    /* Divider styling */
    .stDivider {
        margin: 2rem 0;
    }
    
    /* Success/Error message styling */
    .stSuccess {
        background: linear-gradient(90deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stError {
        background: linear-gradient(90deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stWarning {
        background: linear-gradient(90deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Chart container styling */
    .js-plotly-plot {
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(90deg, #5a6fd8 0%, #6a4190 100%);
    }
</style>
""", unsafe_allow_html=True)


def initialize_data_loader():
    """Initialize data loader and cache in session state"""
    if 'data_loader' not in st.session_state:
        try:
            # Check if processed data exists
            processed_dir = Path("data/processed")
            if not processed_dir.exists():
                processed_dir.mkdir(parents=True, exist_ok=True)
            
            # Check for critical data files
            critical_files = ['institutions.parquet', 'programs.parquet']
            missing_critical = [f for f in critical_files if not (processed_dir / f).exists()]
            
            if missing_critical:
                st.error(f"""
                ⚠️ **Critical data files not found!**
                
                Missing files: {', '.join(missing_critical)}
                
                Please run the ETL pipeline first:
                ```bash
                python -m src.data.etl
                ```
                
                **Required raw data files** (place in `data/raw/` directory):
                - Most-Recent-Cohorts-Institution.csv
                - Most-Recent-Cohorts-Field-of-Study.csv
                - fy2021_safmrs_revised.xlsx through fy2026_safmrs_revised.xlsx
                - cu.data.1.AllItems
                - acs_pums.json
                
                **Note:** The ETL pipeline will create default data for missing files.
                """)
                
                if st.button("🚀 Run ETL Pipeline Now", type="primary"):
                    with st.spinner("Running ETL pipeline..."):
                        try:
                            from src.data.etl import main as run_etl
                            run_etl()
                            st.success("✅ ETL pipeline completed! Refreshing...")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ ETL pipeline failed: {e}")
                st.stop()
            
            # Initialize data loader
            st.session_state.data_loader = DataLoader()
            
        except Exception as e:
            st.error(f"❌ Error initializing data loader: {e}")
            st.error("Please check the console for detailed error messages.")
            st.stop()


def main():
    """Main application entry point"""
    
    # Initialize data loader
    initialize_data_loader()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🎓 College ROI Planner")
        st.markdown("---")
        
        page = st.radio(
            "Navigate",
            options=["Planner", "Compare", "About"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("""
        ### Quick Guide
        
        **Planner:** Analyze a single program's ROI and financial outcomes.
        
        **Compare:** Compare two programs side-by-side.
        
        **About:** Learn about data sources and methodology.
        """)
        
        st.markdown("---")
        st.caption("Version 1.0.0 | MVP")
    
    # Route to appropriate page
    if page == "Planner":
        show_planner_page()
    elif page == "Compare":
        show_compare_page()
    else:
        show_about_page()


if __name__ == "__main__":
    main()

