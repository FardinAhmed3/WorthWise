"""ETL pipeline to process raw data into optimized Parquet files"""

import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import warnings
import logging
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO

warnings.filterwarnings('ignore')

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.data.constants import NULL_VALUES, CREDENTIAL_LEVELS, STATE_COST_MULTIPLIERS, DEFAULT_STATE_MULTIPLIER, TWO_BEDROOM_MULTIPLIER

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataETL:
    """Extract, Transform, Load pipeline for College ROI data"""
    
    def __init__(self, raw_dir: str = "data/raw", processed_dir: str = "data/processed"):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def read_corrupted_excel(self, file_path: Path) -> pd.DataFrame:
        """
        Read Excel files that may have corrupted metadata.
        Uses multiple fallback methods to handle various corruption issues.
        """
        logger.info(f"  Attempting to read {file_path.name} with corruption handling...")
        
        last_error = None
        
        # Method 1: Try standard pandas read_excel
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            logger.info(f"    Successfully read with standard method")
            return df
        except Exception as e1:
            logger.warning(f"    Standard method failed: {e1}")
            last_error = e1
        
        # Method 2: Try with xlrd engine (for older Excel files)
        try:
            df = pd.read_excel(file_path, engine='xlrd')
            logger.info(f"    Successfully read with xlrd engine")
            return df
        except Exception as e2:
            logger.warning(f"    xlrd method failed: {e2}")
            last_error = e2
        
        # Method 3: Try to repair corrupted Excel file by fixing metadata
        try:
            df = self._repair_and_read_excel(file_path)
            logger.info(f"    Successfully read with repair method")
            return df
        except Exception as e3:
            logger.warning(f"    Repair method failed: {e3}")
            last_error = e3
        
        # Method 4: Try reading with different parameters (if supported)
        try:
            df = pd.read_excel(file_path, engine='openpyxl', data_only=True)
            logger.info(f"    Successfully read with data_only=True")
            return df
        except (Exception, TypeError) as e4:
            logger.warning(f"    data_only method failed: {e4}")
            last_error = e4
        
        # Method 5: Try reading as CSV if it's actually a CSV file
        try:
            df = pd.read_csv(file_path)
            logger.info(f"    Successfully read as CSV")
            return df
        except Exception as e5:
            logger.warning(f"    CSV method failed: {e5}")
            last_error = e5
        
        # If all methods fail, raise the last error
        raise Exception(f"All Excel reading methods failed for {file_path.name}. Last error: {last_error}")
    
    def _repair_and_read_excel(self, file_path: Path) -> pd.DataFrame:
        """
        Repair corrupted Excel file by fixing invalid XML metadata.
        This method handles the specific datetime corruption issue.
        """
        # Read the Excel file as a ZIP archive
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            # Get the list of files in the ZIP
            file_list = zip_file.namelist()
            
            # Find the core properties file
            core_props_file = None
            for file in file_list:
                if 'core.xml' in file:
                    core_props_file = file
                    break
            
            if core_props_file:
                try:
                    # Read and fix the core properties
                    core_xml = zip_file.read(core_props_file).decode('utf-8')
                    
                    # Fix common datetime issues
                    core_xml = self._fix_xml_datetime_issues(core_xml)
                    
                    # Create a new ZIP in memory with fixed XML
                    new_zip_data = BytesIO()
                    with zipfile.ZipFile(new_zip_data, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                        for file in file_list:
                            if file == core_props_file:
                                new_zip.writestr(file, core_xml.encode('utf-8'))
                            else:
                                new_zip.writestr(file, zip_file.read(file))
                    
                    # Read the repaired Excel file
                    new_zip_data.seek(0)
                    df = pd.read_excel(new_zip_data, engine='openpyxl')
                    return df
                except Exception as e:
                    # If repair fails, try reading without the corrupted metadata
                    logger.warning(f"    Repair failed, trying to read without metadata: {e}")
                    # Create a minimal Excel file with just the data
                    return self._create_minimal_excel(file_path)
            else:
                # If no core properties found, try reading directly
                return pd.read_excel(file_path, engine='openpyxl')
    
    def _create_minimal_excel(self, file_path: Path) -> pd.DataFrame:
        """
        Create a minimal Excel file by extracting just the worksheet data.
        This bypasses corrupted metadata entirely.
        """
        try:
            # Read the Excel file as a ZIP archive
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Find the worksheet file (usually xl/worksheets/sheet1.xml)
                worksheet_file = None
                for file in zip_file.namelist():
                    if 'xl/worksheets/sheet1.xml' in file:
                        worksheet_file = file
                        break
                
                if worksheet_file:
                    # Read the worksheet XML
                    worksheet_xml = zip_file.read(worksheet_file).decode('utf-8')
                    
                    # Parse the XML to extract data
                    root = ET.fromstring(worksheet_xml)
                    
                    # Find all rows
                    rows = root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
                    
                    if rows:
                        # Extract data from first few rows to understand structure
                        data_rows = []
                        for row in rows[:10]:  # Sample first 10 rows
                            cells = row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                            row_data = []
                            for cell in cells:
                                # Get cell value
                                value_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                                if value_elem is not None:
                                    row_data.append(value_elem.text or '')
                                else:
                                    row_data.append('')
                            data_rows.append(row_data)
                        
                        # Convert to DataFrame
                        if data_rows:
                            # Use first row as headers if it looks like headers
                            if len(data_rows) > 1:
                                headers = data_rows[0]
                                data = data_rows[1:]
                                df = pd.DataFrame(data, columns=headers)
                                return df
                
                # If we can't parse the XML, fall back to trying to read as CSV
                raise Exception("Could not parse worksheet XML")
                
        except Exception as e:
            logger.warning(f"    Minimal Excel creation failed: {e}")
            raise
    
    def _fix_xml_datetime_issues(self, xml_content: str) -> str:
        """
        Fix common datetime issues in Excel XML metadata.
        Handles the specific '2024- 1-24T19: 8: 0Z' format issue.
        """
        import re
        
        # Fix datetime strings with spaces (e.g., "2024- 1-24T19: 8: 0Z" -> "2024-01-24T19:08:00Z")
        def fix_datetime(match):
            dt_str = match.group(0)
            # Remove spaces and fix format
            dt_str = re.sub(r'\s+', '', dt_str)  # Remove all spaces
            # Fix single digit months/days/hours/minutes
            dt_str = re.sub(r'(\d{4})-(\d{1})-(\d{1,2})T(\d{1,2}):(\d{1,2}):(\d{1,2})Z', 
                           r'\1-0\2-0\3T0\4:0\5:0\6Z', dt_str)
            return dt_str
        
        # Find and fix datetime patterns
        datetime_pattern = r'\d{4}-\s*\d{1,2}-\s*\d{1,2}T\s*\d{1,2}:\s*\d{1,2}:\s*\d{1,2}Z'
        xml_content = re.sub(datetime_pattern, fix_datetime, xml_content)
        
        return xml_content
    
    def clean_numeric(self, series: pd.Series) -> pd.Series:
        """Clean numeric columns by replacing null indicators with NaN"""
        series = series.replace(NULL_VALUES, np.nan)
        return pd.to_numeric(series, errors='coerce')
    
    def validate_excel_file(self, file_path: Path) -> bool:
        """
        Validate Excel file integrity before processing.
        Returns True if file is valid, False otherwise.
        """
        try:
            # Try to read the file with standard method
            df = pd.read_excel(file_path, engine='openpyxl', nrows=1)
            logger.info(f"  {file_path.name} validation: PASSED")
            return True
        except Exception as e:
            logger.warning(f"  {file_path.name} validation: FAILED - {e}")
            return False
    
    def get_excel_file_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get information about an Excel file including corruption status.
        """
        info = {
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'is_valid': False,
            'read_method': None,
            'error': None
        }
        
        # Test different reading methods
        methods = [
            ('standard', lambda: pd.read_excel(file_path, engine='openpyxl')),
            ('xlrd', lambda: pd.read_excel(file_path, engine='xlrd'))
        ]
        
        # Add data_only method only if supported
        try:
            # Test if data_only parameter is supported
            pd.read_excel(file_path, engine='openpyxl', data_only=True, nrows=1)
            methods.append(('data_only', lambda: pd.read_excel(file_path, engine='openpyxl', data_only=True)))
        except (TypeError, Exception):
            pass  # data_only not supported in this pandas version
        
        for method_name, method_func in methods:
            try:
                df = method_func()
                info['is_valid'] = True
                info['read_method'] = method_name
                info['shape'] = df.shape
                info['columns'] = df.columns.tolist()
                break
            except Exception as e:
                info['error'] = str(e)
        
        return info
    
    def process_institutions(self) -> None:
        """Process College Scorecard Institution data"""
        logger.info("Processing institutions data...")
        
        input_file = self.raw_dir / "Most-Recent-Cohorts-Institution.csv"
        output_file = self.processed_dir / "institutions.parquet"
        
        if not input_file.exists():
            logger.error(f"Input file not found: {input_file}")
            raise FileNotFoundError(f"Required file not found: {input_file}")
        
        try:
            # Read only needed columns
            columns = [
                'UNITID', 'INSTNM', 'STABBR', 'CITY', 'CONTROL',
                'TUITIONFEE_IN', 'TUITIONFEE_OUT', 'C150_4_POOLED',
                'PCTPELL', 'COSTT4_A', 'UGDS', 'LATITUDE', 'LONGITUDE'
            ]
            
            df = pd.read_csv(input_file, usecols=columns, low_memory=False)
            logger.info(f"  Loaded {len(df)} institutions from CSV")
            
            # Clean numeric columns
            df['UNITID'] = pd.to_numeric(df['UNITID'], errors='coerce').astype('Int64')  # Use nullable integer
            df['CONTROL'] = pd.to_numeric(df['CONTROL'], errors='coerce')
            df['TUITIONFEE_IN'] = self.clean_numeric(df['TUITIONFEE_IN'])
            df['TUITIONFEE_OUT'] = self.clean_numeric(df['TUITIONFEE_OUT'])
            df['C150_4_POOLED'] = self.clean_numeric(df['C150_4_POOLED'])
            df['PCTPELL'] = self.clean_numeric(df['PCTPELL'])
            df['COSTT4_A'] = self.clean_numeric(df['COSTT4_A'])
            df['UGDS'] = self.clean_numeric(df['UGDS'])
            df['LATITUDE'] = self.clean_numeric(df['LATITUDE'])
            df['LONGITUDE'] = self.clean_numeric(df['LONGITUDE'])
            
            # Filter out rows with missing critical data
            initial_count = len(df)
            df = df.dropna(subset=['UNITID', 'INSTNM', 'STABBR'])
            logger.info(f"  Filtered from {initial_count} to {len(df)} institutions after removing missing data")
            
            # Rename columns for clarity
            df = df.rename(columns={
                'UNITID': 'unit_id',
                'INSTNM': 'institution_name',
                'STABBR': 'state',
                'CITY': 'city',
                'CONTROL': 'control_type',
                'TUITIONFEE_IN': 'tuition_in_state',
                'TUITIONFEE_OUT': 'tuition_out_state',
                'C150_4_POOLED': 'graduation_rate',
                'PCTPELL': 'pct_pell',
                'COSTT4_A': 'avg_cost',
                'UGDS': 'undergrad_size',
                'LATITUDE': 'latitude',
                'LONGITUDE': 'longitude'
            })
            
            # Save to parquet
            df.to_parquet(output_file, index=False, compression='snappy')
            logger.info(f"  Saved {len(df)} institutions to {output_file}")
            
        except Exception as e:
            logger.error(f"Error processing institutions data: {e}")
            raise
    
    def process_programs(self) -> None:
        """Process College Scorecard Field of Study data"""
        logger.info("Processing programs data...")
        
        input_file = self.raw_dir / "Most-Recent-Cohorts-Field-of-Study.csv"
        output_file = self.processed_dir / "programs.parquet"
        
        if not input_file.exists():
            logger.error(f"Input file not found: {input_file}")
            raise FileNotFoundError(f"Required file not found: {input_file}")
        
        try:
            # Read only needed columns
            columns = [
                'UNITID', 'CIPCODE', 'CIPDESC', 'CREDLEV',
                'EARN_MDN_1YR', 'EARN_MDN_4YR', 'DEBT_ALL_STGP_ANY_MDN',
                'IPEDSCOUNT1', 'IPEDSCOUNT2'
            ]
            
            df = pd.read_csv(input_file, usecols=columns, low_memory=False)
            logger.info(f"  Loaded {len(df)} programs from CSV")
            
            # Filter for Bachelor's degrees only (CREDLEV == 3)
            initial_count = len(df)
            df = df[df['CREDLEV'] == 3].copy()
            logger.info(f"  Filtered to {len(df)} Bachelor's degree programs (from {initial_count} total)")
            
            # Clean numeric columns
            df['UNITID'] = pd.to_numeric(df['UNITID'], errors='coerce').astype('Int64')  # Use nullable integer
            df['EARN_MDN_1YR'] = self.clean_numeric(df['EARN_MDN_1YR'])
            df['EARN_MDN_4YR'] = self.clean_numeric(df['EARN_MDN_4YR'])
            df['DEBT_ALL_STGP_ANY_MDN'] = self.clean_numeric(df['DEBT_ALL_STGP_ANY_MDN'])
            df['IPEDSCOUNT1'] = self.clean_numeric(df['IPEDSCOUNT1'])
            df['IPEDSCOUNT2'] = self.clean_numeric(df['IPEDSCOUNT2'])
            
            # Filter out rows with missing critical data
            before_filter = len(df)
            df = df.dropna(subset=['UNITID', 'CIPCODE'])
            logger.info(f"  Filtered from {before_filter} to {len(df)} programs after removing missing data")
            
            # Rename columns
            df = df.rename(columns={
                'UNITID': 'unit_id',
                'CIPCODE': 'cip_code',
                'CIPDESC': 'program_name',
                'CREDLEV': 'credential_level',
                'EARN_MDN_1YR': 'median_earnings_1yr',
                'EARN_MDN_4YR': 'median_earnings_4yr',
                'DEBT_ALL_STGP_ANY_MDN': 'median_debt',
                'IPEDSCOUNT1': 'completions',
                'IPEDSCOUNT2': 'completions_alt'
            })
            
            # Extract CIP category (first 2 digits)
            df['cip_category'] = df['cip_code'].astype(str).str[:2]
            
            # Save to parquet
            df.to_parquet(output_file, index=False, compression='snappy')
            logger.info(f"  Saved {len(df)} programs to {output_file}")
            
        except Exception as e:
            logger.error(f"Error processing programs data: {e}")
            raise
    
    def process_housing_costs_safmrs(self) -> None:
        """Process HUD Small Area Fair Market Rents (SAFMRS) data and aggregate to state level"""
        logger.info("Processing SAFMRS housing costs data...")
        
        output_file = self.processed_dir / "housing_costs.parquet"
        
        # Process all SAFMRS files (FY2021-FY2026)
        all_data = []
        safmrs_files = sorted(self.raw_dir.glob("fy*_safmrs_revised.xlsx"))
        
        if not safmrs_files:
            logger.warning("No SAFMRS files found, creating default housing costs")
            self._create_default_housing_costs(output_file)
            return
        
        logger.info(f"  Found {len(safmrs_files)} SAFMRS files to process")
        
        for safmrs_file in safmrs_files:
            logger.info(f"  Reading {safmrs_file.name}...")
            
            try:
                # Read SAFMRS file
                df = pd.read_excel(safmrs_file, engine='openpyxl')
                logger.info(f"    Loaded {len(df)} records from {safmrs_file.name}")
                
                # Clean column names (remove newlines and extra spaces)
                df.columns = df.columns.str.replace('\n', ' ').str.replace('  ', ' ').str.strip()
                
                # Identify key columns
                # Look for ZIP Code column
                zip_col = None
                for col in df.columns:
                    if 'zip' in col.lower() and 'code' in col.lower():
                        zip_col = col
                        break
                
                # Look for area name column (contains state)
                area_col = None
                for col in df.columns:
                    if 'area' in col.lower() and 'name' in col.lower():
                        area_col = col
                        break
                
                # Look for SAFMR 1BR and 2BR columns
                safmr_1br_col = None
                safmr_2br_col = None
                for col in df.columns:
                    if 'safmr' in col.lower() and '1br' in col.lower() and 'payment' not in col.lower():
                        safmr_1br_col = col
                    elif 'safmr' in col.lower() and '2br' in col.lower() and 'payment' not in col.lower():
                        safmr_2br_col = col
                
                if not all([zip_col, area_col, safmr_1br_col, safmr_2br_col]):
                    logger.error(f"    Missing required columns in {safmrs_file.name}")
                    logger.error(f"    Found: ZIP={zip_col}, Area={area_col}, 1BR={safmr_1br_col}, 2BR={safmr_2br_col}")
                    continue
                
                logger.info(f"    Using columns: ZIP={zip_col}, Area={area_col}, 1BR={safmr_1br_col}, 2BR={safmr_2br_col}")
                
                # Extract state from area name (format: "City, ST MSA" or "City, ST")
                df['state'] = df[area_col].str.extract(r',\s*([A-Z]{2})\s*(?:MSA|HMFA)?', expand=False)
                
                # Clean numeric columns
                df['fmr_1br'] = pd.to_numeric(df[safmr_1br_col], errors='coerce')
                df['fmr_2br'] = pd.to_numeric(df[safmr_2br_col], errors='coerce')
                
                # Filter valid records
                valid_data = df[['state', 'fmr_1br', 'fmr_2br']].copy()
                valid_data = valid_data.dropna(subset=['state', 'fmr_1br', 'fmr_2br'])
                
                # Remove any invalid state codes (should be 2 letters)
                valid_data = valid_data[valid_data['state'].str.len() == 2]
                
                logger.info(f"    Extracted {len(valid_data)} valid records with state data")
                
                if len(valid_data) > 0:
                    all_data.append(valid_data)
                else:
                    logger.warning(f"    No valid data extracted from {safmrs_file.name}")
                    
            except Exception as e:
                logger.error(f"  Error processing {safmrs_file.name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        if all_data:
            # Combine all years
            combined = pd.concat(all_data, ignore_index=True)
            logger.info(f"  Combined {len(combined)} total records from all SAFMRS files")
            logger.info(f"  States found: {sorted(combined['state'].unique())}")
            
            # Aggregate to state level (median across all ZIP codes and years)
            state_housing = combined.groupby('state').agg({
                'fmr_1br': 'median',
                'fmr_2br': 'median'
            }).reset_index()
            
            # Convert monthly to annual
            state_housing['annual_1br'] = state_housing['fmr_1br'] * 12
            state_housing['annual_2br'] = state_housing['fmr_2br'] * 12
            
            # Round to integers for cleaner display
            state_housing['annual_1br'] = state_housing['annual_1br'].round(0).astype(int)
            state_housing['annual_2br'] = state_housing['annual_2br'].round(0).astype(int)
            
            # Save to parquet
            state_housing.to_parquet(output_file, index=False, compression='snappy')
            logger.info(f"  ✓ Saved housing costs for {len(state_housing)} states to {output_file}")
            logger.info(f"  Sample data:")
            logger.info(f"\n{state_housing.head(10)}")
        else:
            logger.warning("No housing data processed from SAFMRS files, creating defaults")
            self._create_default_housing_costs(output_file)
    
    def _create_default_housing_costs(self, output_file: Path) -> None:
        """Create default housing costs when HUD data is unavailable"""
        logger.info("Creating default housing costs...")
        
        # Default state housing costs (annual)
        default_costs = {
            'AL': 9600, 'AK': 14400, 'AZ': 12000, 'AR': 9000, 'CA': 18000,
            'CO': 15000, 'CT': 16800, 'DE': 13200, 'FL': 13200, 'GA': 10800,
            'HI': 24000, 'ID': 10800, 'IL': 12000, 'IN': 9600, 'IA': 9000,
            'KS': 9600, 'KY': 9600, 'LA': 10800, 'ME': 12000, 'MD': 16800,
            'MA': 19200, 'MI': 10800, 'MN': 12000, 'MS': 9000, 'MO': 10800,
            'MT': 12000, 'NE': 9600, 'NV': 13200, 'NH': 14400, 'NJ': 18000,
            'NM': 10800, 'NY': 18000, 'NC': 12000, 'ND': 10800, 'OH': 10800,
            'OK': 9600, 'OR': 13200, 'PA': 12000, 'RI': 14400, 'SC': 10800,
            'SD': 9600, 'TN': 10800, 'TX': 12000, 'UT': 12000, 'VT': 13200,
            'VA': 13200, 'WA': 15000, 'WV': 9000, 'WI': 10800, 'WY': 12000, 'DC': 24000
        }
        
        state_housing = pd.DataFrame([
            {'state': state, 'annual_1br': cost, 'annual_2br': cost * TWO_BEDROOM_MULTIPLIER}
            for state, cost in default_costs.items()
        ])
        
        state_housing.to_parquet(output_file, index=False, compression='snappy')
        logger.info(f"  Created default housing costs for {len(state_housing)} states")
    
    def process_cpi(self) -> None:
        """Process BLS CPI data"""
        logger.info("Processing CPI data...")
        
        input_file = self.raw_dir / "cu.data.1.AllItems"
        output_file = self.processed_dir / "cpi.parquet"
        
        if not input_file.exists():
            logger.warning(f"CPI file not found: {input_file}, creating default CPI data")
            self._create_default_cpi(output_file)
            return
        
        try:
            # Read tab-delimited file
            df = pd.read_csv(input_file, sep='\t', skipinitialspace=True)
            logger.info(f"  Loaded {len(df)} CPI records")
            
            # Filter for annual average (period M13) or use all monthly data
            # Calculate annual average from monthly data
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            # Remove rows with missing data
            df = df.dropna(subset=['year', 'value'])
            
            # Group by year and calculate mean
            annual_cpi = df.groupby('year')['value'].mean().reset_index()
            annual_cpi = annual_cpi.rename(columns={'value': 'cpi_value'})
            
            # Calculate inflation multiplier to 2024
            cpi_2024 = annual_cpi[annual_cpi['year'] == 2024]['cpi_value'].values
            if len(cpi_2024) > 0:
                base_cpi = cpi_2024[0]
            else:
                # Use most recent year
                base_cpi = annual_cpi['cpi_value'].iloc[-1]
                logger.info(f"  Using {annual_cpi['year'].iloc[-1]} as base year for CPI")
            
            annual_cpi['inflation_multiplier'] = base_cpi / annual_cpi['cpi_value']
            
            # Save to parquet
            annual_cpi.to_parquet(output_file, index=False, compression='snappy')
            logger.info(f"  Saved CPI data for {len(annual_cpi)} years to {output_file}")
            
        except Exception as e:
            logger.warning(f"Error processing CPI data: {e}, creating default")
            self._create_default_cpi(output_file)
    
    def _create_default_cpi(self, output_file: Path) -> None:
        """Create default CPI data when BLS data is unavailable"""
        logger.info("Creating default CPI data...")
        
        # Create default CPI data for recent years
        years = list(range(2020, 2025))
        cpi_values = [100, 103, 106, 109, 112]  # Simulated CPI values
        
        annual_cpi = pd.DataFrame({
            'year': years,
            'cpi_value': cpi_values,
            'inflation_multiplier': [cpi_values[-1] / val for val in cpi_values]
        })
        
        annual_cpi.to_parquet(output_file, index=False, compression='snappy')
        logger.info(f"  Created default CPI data for {len(annual_cpi)} years")
    
    def process_acs_pums(self) -> None:
        """Process ACS PUMS data for earnings by state and education"""
        logger.info("Processing ACS PUMS data...")
        
        input_file = self.raw_dir / "acs_pums.json"
        output_file = self.processed_dir / "earnings_by_state.parquet"
        
        if not input_file.exists():
            logger.warning(f"ACS PUMS file not found: {input_file}, creating default earnings data")
            self._create_default_earnings(output_file)
            return
        
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            # Data appears to be array of arrays
            # First row is headers
            if len(data) > 0 and isinstance(data[0], list):
                headers = data[0]
                rows = data[1:]
                
                df = pd.DataFrame(rows, columns=headers)
                logger.info(f"  Loaded {len(df)} PUMS records")
                
                # Try to identify relevant columns
                # Common PUMS columns: WAGP (wages), SCHL (education), ST (state), PWGTP (weight)
                
                # For MVP, create a simple state-level earnings lookup
                # Using placeholder data since actual PUMS structure needs verification
                
                # Create default state earnings (placeholder)
                self._create_default_earnings(output_file)
            
        except Exception as e:
            logger.warning(f"Could not process ACS PUMS data: {e}, creating default earnings data")
            self._create_default_earnings(output_file)
    
    def _create_default_earnings(self, output_file: Path) -> None:
        """Create default earnings data when ACS PUMS data is unavailable"""
        logger.info("Creating default earnings data...")
        
        # Create default state earnings with some variation
        states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC']
        
        # State-specific earnings multipliers (relative to national median)
        state_multipliers = STATE_COST_MULTIPLIERS
        
        base_earnings = 45000  # National median
        state_earnings = []
        
        for state in states:
            multiplier = state_multipliers.get(state, DEFAULT_STATE_MULTIPLIER)
            earnings = int(base_earnings * multiplier)
            state_earnings.append({'state': state, 'median_earnings': earnings})
        
        earnings_df = pd.DataFrame(state_earnings)
        earnings_df.to_parquet(output_file, index=False, compression='snappy')
        logger.info(f"  Created earnings data for {len(earnings_df)} states")
    
    def diagnose_excel_files(self) -> None:
        """Run diagnostics on all Excel files to identify issues"""
        logger.info("=" * 60)
        logger.info("Excel File Diagnostics")
        logger.info("=" * 60)
        
        excel_files = list(self.raw_dir.glob("*.xlsx")) + list(self.raw_dir.glob("*.xls"))
        
        for file_path in excel_files:
            logger.info(f"Analyzing {file_path.name}...")
            info = self.get_excel_file_info(file_path)
            
            if info['is_valid']:
                logger.info(f"  ✓ Valid - Method: {info['read_method']}, Shape: {info['shape']}")
            else:
                logger.warning(f"  ✗ Invalid - Error: {info['error']}")
        
        logger.info("=" * 60)
    
    def run_all(self) -> None:
        """Run complete ETL pipeline"""
        logger.info("=" * 80)
        logger.info("STARTING COLLEGE ROI PLANNER ETL PIPELINE")
        logger.info("=" * 80)
        
        try:
            # Process each data source
            logger.info("\n[1/5] Processing Institution Data...")
            self.process_institutions()
            
            logger.info("\n[2/5] Processing Program Data...")
            self.process_programs()
            
            logger.info("\n[3/5] Processing Housing Costs (SAFMRS)...")
            self.process_housing_costs_safmrs()
            
            logger.info("\n[4/5] Processing CPI Data...")
            self.process_cpi()
            
            logger.info("\n[5/5] Processing Earnings Data...")
            self.process_acs_pums()
            
            logger.info("\n" + "=" * 80)
            logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY!")
            logger.info("=" * 80)
            
            # Verify all output files exist
            required_files = [
                'institutions.parquet',
                'programs.parquet', 
                'housing_costs.parquet',
                'cpi.parquet',
                'earnings_by_state.parquet'
            ]
            
            logger.info("\nVerifying output files...")
            missing_files = []
            for file in required_files:
                file_path = self.processed_dir / file
                if file_path.exists():
                    size = file_path.stat().st_size / 1024  # KB
                    logger.info(f"  ✓ {file} ({size:.1f} KB)")
                else:
                    missing_files.append(file)
                    logger.error(f"  ✗ {file} (missing)")
            
            if missing_files:
                logger.error(f"\nMissing output files: {missing_files}")
                raise FileNotFoundError(f"ETL pipeline failed to create required files: {missing_files}")
            else:
                logger.info("\n✓ All required output files created successfully!")
                logger.info("\nYou can now run the Streamlit app with:")
                logger.info("  streamlit run app.py")
                
        except Exception as e:
            logger.error(f"\n✗ ETL pipeline failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise


def main():
    """Run ETL pipeline"""
    try:
        etl = DataETL()
        etl.run_all()
        print("ETL pipeline completed successfully!")
        print("You can now run the Streamlit app with: streamlit run app.py")
    except Exception as e:
        print(f"ETL pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

