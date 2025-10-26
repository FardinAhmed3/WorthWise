"""Data validation utilities for College ROI Planner"""

import pandas as pd
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class DataValidator:
    """Utility class for data validation and integrity checks"""
    
    @staticmethod
    def validate_institution_program_linkage(institutions_df: pd.DataFrame, programs_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate that institutions and programs data can be properly linked.
        
        Args:
            institutions_df: DataFrame of institutions
            programs_df: DataFrame of programs
            
        Returns:
            Dictionary with validation results and statistics
        """
        # Get unique unit_ids from both datasets
        inst_unit_ids = set(institutions_df['unit_id'].dropna().astype(int))
        prog_unit_ids = set(programs_df['unit_id'].dropna().astype(int))
        
        # Find common unit_ids
        common_unit_ids = inst_unit_ids.intersection(prog_unit_ids)
        
        # Calculate statistics
        total_institutions = len(inst_unit_ids)
        total_programs = len(prog_unit_ids)
        linked_institutions = len(common_unit_ids)
        orphaned_institutions = len(inst_unit_ids - prog_unit_ids)
        orphaned_programs = len(prog_unit_ids - inst_unit_ids)
        
        validation_result = {
            'is_valid': len(common_unit_ids) > 0,
            'total_institutions': total_institutions,
            'total_programs': total_programs,
            'linked_institutions': linked_institutions,
            'orphaned_institutions': orphaned_institutions,
            'orphaned_programs': orphaned_programs,
            'linkage_rate': linked_institutions / total_institutions if total_institutions > 0 else 0,
            'common_unit_ids': list(common_unit_ids)[:10]  # First 10 for debugging
        }
        
        logger.info(f"Data linkage validation: {linked_institutions}/{total_institutions} institutions have programs")
        
        return validation_result
    
    @staticmethod
    def get_sample_programs_for_institution(programs_df: pd.DataFrame, unit_id: int, limit: int = 5) -> pd.DataFrame:
        """
        Get sample programs for a specific institution.
        
        Args:
            programs_df: DataFrame of programs
            unit_id: Institution unit ID
            limit: Maximum number of programs to return
            
        Returns:
            DataFrame of sample programs
        """
        # Try exact match first
        exact_match = programs_df[programs_df['unit_id'] == unit_id]
        if len(exact_match) > 0:
            return exact_match.head(limit)
        
        # Try with type casting
        try:
            cast_match = programs_df[programs_df['unit_id'].astype(int) == unit_id]
            if len(cast_match) > 0:
                return cast_match.head(limit)
        except Exception as e:
            logger.warning(f"Type casting failed for unit_id {unit_id}: {e}")
        
        # Return empty DataFrame if no match
        return pd.DataFrame()
    
    @staticmethod
    def validate_data_quality(df: pd.DataFrame, required_columns: List[str], table_name: str) -> Dict[str, Any]:
        """
        Validate data quality for a DataFrame.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            table_name: Name of the table for logging
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'is_valid': True,
            'total_rows': len(df),
            'missing_columns': [],
            'null_counts': {},
            'duplicate_rows': 0
        }
        
        # Check for missing columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        validation_result['missing_columns'] = missing_columns
        
        if missing_columns:
            validation_result['is_valid'] = False
            logger.error(f"{table_name}: Missing required columns: {missing_columns}")
        
        # Check for null values in required columns
        for col in required_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                validation_result['null_counts'][col] = null_count
                if null_count > 0:
                    logger.warning(f"{table_name}: Column '{col}' has {null_count} null values")
        
        # Check for duplicate rows
        duplicate_count = df.duplicated().sum()
        validation_result['duplicate_rows'] = duplicate_count
        if duplicate_count > 0:
            logger.warning(f"{table_name}: Found {duplicate_count} duplicate rows")
        
        return validation_result
    
    @staticmethod
    def create_fallback_program_data(unit_id: int, institution_name: str) -> Dict[str, Any]:
        """
        Create fallback program data when no programs are found for an institution.
        
        Args:
            unit_id: Institution unit ID
            institution_name: Institution name
            
        Returns:
            Dictionary with fallback program data
        """
        fallback_programs = [
            {
                'unit_id': unit_id,
                'cip_code': '520000',
                'program_name': 'Business Administration and Management, General',
                'credential_level': 3,
                'median_earnings_1yr': 45000,
                'median_earnings_4yr': 50000,
                'median_debt': 25000,
                'cip_category': '52'
            },
            {
                'unit_id': unit_id,
                'cip_code': '110000',
                'program_name': 'Computer and Information Sciences, General',
                'credential_level': 3,
                'median_earnings_1yr': 55000,
                'median_earnings_4yr': 65000,
                'median_debt': 28000,
                'cip_category': '11'
            },
            {
                'unit_id': unit_id,
                'cip_code': '140000',
                'program_name': 'Engineering, General',
                'credential_level': 3,
                'median_earnings_1yr': 60000,
                'median_earnings_4yr': 75000,
                'median_debt': 30000,
                'cip_category': '14'
            }
        ]
        
        logger.info(f"Created {len(fallback_programs)} fallback programs for {institution_name}")
        return fallback_programs
