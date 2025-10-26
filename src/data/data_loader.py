"""Data access layer using DuckDB for fast querying"""

import duckdb
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any
import streamlit as st
import logging

from .validation import DataValidator

logger = logging.getLogger(__name__)


class DataLoader:
    """DuckDB-based data access layer for College ROI data"""
    
    def __init__(self, data_dir: str = "data/processed"):
        self.data_dir = Path(data_dir)
        self.conn = duckdb.connect(":memory:")
        self._load_tables()
    
    def _load_tables(self) -> None:
        """Register all parquet files as DuckDB tables"""
        try:
            # Register institutions
            institutions_file = self.data_dir / "institutions.parquet"
            if institutions_file.exists():
                self.conn.execute(f"""
                    CREATE TABLE institutions AS 
                    SELECT * FROM read_parquet('{institutions_file}')
                """)
                st.success(f"✅ Loaded institutions data ({institutions_file})")
            else:
                st.error(f"❌ Institutions file not found: {institutions_file}")
                return
            
            # Register programs
            programs_file = self.data_dir / "programs.parquet"
            if programs_file.exists():
                self.conn.execute(f"""
                    CREATE TABLE programs AS 
                    SELECT * FROM read_parquet('{programs_file}')
                """)
                st.success(f"✅ Loaded programs data ({programs_file})")
            else:
                st.error(f"❌ Programs file not found: {programs_file}")
                return
            
            # Register housing costs
            housing_file = self.data_dir / "housing_costs.parquet"
            if housing_file.exists():
                self.conn.execute(f"""
                    CREATE TABLE housing_costs AS 
                    SELECT * FROM read_parquet('{housing_file}')
                """)
                st.success(f"✅ Loaded housing costs data ({housing_file})")
            else:
                st.warning(f"⚠️ Housing costs file not found: {housing_file}")
                # Create default housing costs table
                self._create_default_housing_table()
            
            # Register CPI
            cpi_file = self.data_dir / "cpi.parquet"
            if cpi_file.exists():
                self.conn.execute(f"""
                    CREATE TABLE cpi AS 
                    SELECT * FROM read_parquet('{cpi_file}')
                """)
                st.success(f"✅ Loaded CPI data ({cpi_file})")
            else:
                st.warning(f"⚠️ CPI file not found: {cpi_file}")
                # Create default CPI table
                self._create_default_cpi_table()
            
            # Register earnings
            earnings_file = self.data_dir / "earnings_by_state.parquet"
            if earnings_file.exists():
                self.conn.execute(f"""
                    CREATE TABLE earnings_by_state AS 
                    SELECT * FROM read_parquet('{earnings_file}')
                """)
                st.success(f"✅ Loaded earnings data ({earnings_file})")
            else:
                st.warning(f"⚠️ Earnings file not found: {earnings_file}")
                # Create default earnings table
                self._create_default_earnings_table()
                
        except Exception as e:
            st.error(f"❌ Error loading data tables: {e}")
            st.error("Please run the ETL pipeline first: `python -m src.data.etl`")
    
    def _create_default_housing_table(self) -> None:
        """Create default housing costs table"""
        self.conn.execute("""
            CREATE TABLE housing_costs AS 
            SELECT 'CA' as state, 18000 as annual_1br, 23400 as annual_2br
            UNION ALL SELECT 'NY', 18000, 23400
            UNION ALL SELECT 'TX', 12000, 15600
            UNION ALL SELECT 'FL', 13200, 17160
            UNION ALL SELECT 'IL', 12000, 15600
        """)
        st.info("📊 Created default housing costs table")
    
    def _create_default_cpi_table(self) -> None:
        """Create default CPI table"""
        self.conn.execute("""
            CREATE TABLE cpi AS 
            SELECT 2024 as year, 100.0 as cpi_value, 1.0 as inflation_multiplier
        """)
        st.info("📊 Created default CPI table")
    
    def _create_default_earnings_table(self) -> None:
        """Create default earnings table"""
        self.conn.execute("""
            CREATE TABLE earnings_by_state AS 
            SELECT 'CA' as state, 58500 as median_earnings
            UNION ALL SELECT 'NY', 56250
            UNION ALL SELECT 'TX', 45000
            UNION ALL SELECT 'FL', 42750
            UNION ALL SELECT 'IL', 47250
        """)
        st.info("📊 Created default earnings table")
    
    def validate_data_linkage(self) -> Dict[str, Any]:
        """Validate that institutions and programs data can be properly linked"""
        try:
            institutions_df = self.conn.execute("SELECT * FROM institutions").fetchdf()
            programs_df = self.conn.execute("SELECT * FROM programs").fetchdf()
            
            validation_result = DataValidator.validate_institution_program_linkage(
                institutions_df, programs_df
            )
            
            if not validation_result['is_valid']:
                st.warning(f"⚠️ Data linkage issue: Only {validation_result['linked_institutions']} institutions have programs")
                logger.warning(f"Data linkage validation failed: {validation_result}")
            
            return validation_result
        except Exception as e:
            logger.error(f"Error validating data linkage: {e}")
            return {'is_valid': False, 'error': str(e)}
    
    def create_fallback_programs_for_institution(self, unit_id: int, institution_name: str) -> pd.DataFrame:
        """Create fallback programs for an institution when no programs are found"""
        try:
            fallback_data = DataValidator.create_fallback_program_data(unit_id, institution_name)
            fallback_df = pd.DataFrame(fallback_data)
            
            # Insert fallback programs into the database
            for _, row in fallback_df.iterrows():
                self.conn.execute(f"""
                    INSERT INTO programs 
                    (unit_id, cip_code, program_name, credential_level, 
                     median_earnings_1yr, median_earnings_4yr, median_debt, cip_category)
                    VALUES ({row['unit_id']}, '{row['cip_code']}', '{row['program_name']}', 
                            {row['credential_level']}, {row['median_earnings_1yr']}, 
                            {row['median_earnings_4yr']}, {row['median_debt']}, '{row['cip_category']}')
                """)
            
            logger.info(f"Created {len(fallback_df)} fallback programs for {institution_name}")
            return fallback_df
            
        except Exception as e:
            logger.error(f"Error creating fallback programs for {institution_name}: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=3600)
    def get_institutions(_self, state: Optional[str] = None) -> pd.DataFrame:
        """
        Query institutions with optional state filter.
        
        Args:
            state: State abbreviation filter (optional)
        
        Returns:
            DataFrame of institutions
        """
        query = "SELECT * FROM institutions WHERE 1=1"
        
        if state:
            query += f" AND state = '{state}'"
        
        query += " ORDER BY institution_name"
        
        try:
            result = _self.conn.execute(query).fetchdf()
            return result
        except Exception as e:
            st.error(f"Error querying institutions: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=3600)
    def get_states(_self) -> List[str]:
        """Get list of all states with institutions."""
        try:
            result = _self.conn.execute("""
                SELECT DISTINCT state 
                FROM institutions 
                WHERE state IS NOT NULL 
                ORDER BY state
            """).fetchdf()
            return result['state'].tolist()
        except Exception as e:
            st.error(f"Error querying states: {e}")
            return []
    
    @st.cache_data(ttl=3600)
    def get_programs(_self, unit_id: int) -> pd.DataFrame:
        """
        Get all programs for an institution.
        
        Args:
            unit_id: Institution UNITID
        
        Returns:
            DataFrame of programs
        """
        try:
            # Convert unit_id to int to handle type mismatches
            unit_id = int(unit_id)
            
            result = _self.conn.execute(f"""
                SELECT * FROM programs 
                WHERE unit_id = {unit_id}
                ORDER BY program_name
            """).fetchdf()
            
            if len(result) == 0:
                logger.warning(f"No programs found for unit_id {unit_id}")
                # Try to find programs with similar unit_id (in case of data type issues)
                result = _self.conn.execute(f"""
                    SELECT * FROM programs 
                    WHERE CAST(unit_id AS INTEGER) = {unit_id}
                    ORDER BY program_name
                """).fetchdf()
            
            # If still no programs found, create fallback programs
            if len(result) == 0:
                # Get institution name for fallback
                inst_details = _self.get_institution_details(unit_id)
                if inst_details:
                    institution_name = inst_details.get('institution_name', f'Institution {unit_id}')
                    logger.info(f"Creating fallback programs for {institution_name}")
                    result = _self.create_fallback_programs_for_institution(unit_id, institution_name)
                else:
                    logger.error(f"Cannot create fallback programs: institution details not found for unit_id {unit_id}")
            
            return result
        except Exception as e:
            logger.error(f"Error querying programs for unit_id {unit_id}: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=3600)
    def get_institution_details(_self, unit_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific institution.
        
        Args:
            unit_id: Institution UNITID
        
        Returns:
            Dictionary of institution details or None
        """
        try:
            result = _self.conn.execute(f"""
                SELECT * FROM institutions 
                WHERE unit_id = {unit_id}
            """).fetchdf()
            
            if len(result) > 0:
                return result.iloc[0].to_dict()
            return None
        except Exception as e:
            st.error(f"Error querying institution details: {e}")
            return None
    
    @st.cache_data(ttl=3600)
    def get_program_details(_self, unit_id: int, cip_code: str) -> Optional[Dict[str, Any]]:
        """
        Get specific program details with earnings and debt data.
        
        Args:
            unit_id: Institution UNITID
            cip_code: CIP code for the program
        
        Returns:
            Dictionary of program details or None
        """
        try:
            # Convert unit_id to int to handle type mismatches
            unit_id = int(unit_id)
            
            result = _self.conn.execute(f"""
                SELECT * FROM programs 
                WHERE unit_id = {unit_id} AND cip_code = '{cip_code}'
            """).fetchdf()
            
            if len(result) > 0:
                return result.iloc[0].to_dict()
            
            # Try with type casting if no results
            result = _self.conn.execute(f"""
                SELECT * FROM programs 
                WHERE CAST(unit_id AS INTEGER) = {unit_id} AND cip_code = '{cip_code}'
            """).fetchdf()
            
            if len(result) > 0:
                return result.iloc[0].to_dict()
            
            logger.warning(f"No program found for unit_id {unit_id} and cip_code {cip_code}")
            return None
        except Exception as e:
            logger.error(f"Error querying program details for unit_id {unit_id}, cip_code {cip_code}: {e}")
            return None
    
    @st.cache_data(ttl=3600)
    def get_state_housing_cost(_self, state: str) -> float:
        """
        Get median 1BR annual rent for state.
        
        Args:
            state: State abbreviation
        
        Returns:
            Annual 1BR rent (defaults to $12,000 if not found)
        """
        try:
            result = _self.conn.execute(f"""
                SELECT annual_1br FROM housing_costs 
                WHERE state = '{state}'
            """).fetchdf()
            
            if len(result) > 0 and pd.notna(result.iloc[0]['annual_1br']):
                return float(result.iloc[0]['annual_1br'])
            return 12000.0  # Default fallback
        except Exception as e:
            return 12000.0  # Default fallback
    
    @st.cache_data(ttl=3600)
    def get_cpi_multiplier(_self, base_year: int = 2020) -> float:
        """
        Get inflation adjustment factor from base year to current.
        
        Args:
            base_year: Base year for adjustment
        
        Returns:
            Inflation multiplier
        """
        try:
            result = _self.conn.execute(f"""
                SELECT inflation_multiplier FROM cpi 
                WHERE year = {base_year}
            """).fetchdf()
            
            if len(result) > 0:
                return float(result.iloc[0]['inflation_multiplier'])
            return 1.0  # No adjustment if not found
        except Exception as e:
            return 1.0
    
    @st.cache_data(ttl=3600)
    def get_state_earnings(_self, state: str) -> float:
        """
        Get median earnings for state.
        
        Args:
            state: State abbreviation
        
        Returns:
            Median earnings (defaults to $45,000 if not found)
        """
        try:
            result = _self.conn.execute(f"""
                SELECT median_earnings FROM earnings_by_state 
                WHERE state = '{state}'
            """).fetchdf()
            
            if len(result) > 0 and pd.notna(result.iloc[0]['median_earnings']):
                return float(result.iloc[0]['median_earnings'])
            return 45000.0  # Default fallback
        except Exception as e:
            return 45000.0
    
    @st.cache_data(ttl=3600)
    def search_institutions(_self, search_term: str, limit: int = 50) -> pd.DataFrame:
        """
        Search institutions by name.
        
        Args:
            search_term: Search string
            limit: Maximum results to return
        
        Returns:
            DataFrame of matching institutions
        """
        try:
            search_term = search_term.replace("'", "''")  # Escape quotes
            result = _self.conn.execute(f"""
                SELECT * FROM institutions 
                WHERE LOWER(institution_name) LIKE LOWER('%{search_term}%')
                ORDER BY institution_name
                LIMIT {limit}
            """).fetchdf()
            return result
        except Exception as e:
            st.error(f"Error searching institutions: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=3600)
    def get_institution_programs_summary(_self, unit_id: int) -> Dict[str, Any]:
        """
        Get summary statistics for institution's programs.
        
        Args:
            unit_id: Institution UNITID
        
        Returns:
            Dictionary with summary stats
        """
        try:
            result = _self.conn.execute(f"""
                SELECT 
                    COUNT(*) as program_count,
                    AVG(median_earnings_1yr) as avg_earnings_1yr,
                    AVG(median_debt) as avg_debt
                FROM programs 
                WHERE unit_id = {unit_id}
            """).fetchdf()
            
            if len(result) > 0:
                return result.iloc[0].to_dict()
            return {'program_count': 0, 'avg_earnings_1yr': None, 'avg_debt': None}
        except Exception as e:
            return {'program_count': 0, 'avg_earnings_1yr': None, 'avg_debt': None}
    
    def close(self) -> None:
        """Close database connection"""
        if self.conn:
            self.conn.close()

