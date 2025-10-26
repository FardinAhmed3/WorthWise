"""Constants and default values for the College ROI Planner"""

# Null value indicators from College Scorecard
NULL_VALUES = ['NULL', 'PrivacySuppressed', '', 'NA', 'N/A', None]

# State abbreviation to full name mapping
US_STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
    'PR': 'Puerto Rico', 'VI': 'Virgin Islands', 'GU': 'Guam', 'AS': 'American Samoa'
}

# CIP code major category mappings (first 2 digits)
CIP_CATEGORIES = {
    '01': 'Agriculture',
    '03': 'Natural Resources',
    '04': 'Architecture',
    '05': 'Area/Ethnic Studies',
    '09': 'Communication',
    '10': 'Communications Technologies',
    '11': 'Computer Science',
    '12': 'Personal Services',
    '13': 'Education',
    '14': 'Engineering',
    '15': 'Engineering Technologies',
    '16': 'Foreign Languages',
    '19': 'Family/Consumer Sciences',
    '22': 'Legal Professions',
    '23': 'English Language',
    '24': 'Liberal Arts',
    '25': 'Library Science',
    '26': 'Biological Sciences',
    '27': 'Mathematics',
    '29': 'Military Technologies',
    '30': 'Multi/Interdisciplinary',
    '31': 'Parks/Recreation',
    '38': 'Philosophy/Religious',
    '39': 'Theology',
    '40': 'Physical Sciences',
    '41': 'Science Technologies',
    '42': 'Psychology',
    '43': 'Homeland Security',
    '44': 'Public Administration',
    '45': 'Social Sciences',
    '46': 'Construction Trades',
    '47': 'Mechanic/Repair',
    '48': 'Precision Production',
    '49': 'Transportation',
    '50': 'Visual/Performing Arts',
    '51': 'Health Professions',
    '52': 'Business/Management',
    '54': 'History'
}

# Institution control types
CONTROL_TYPES = {
    1: 'Public',
    2: 'Private nonprofit',
    3: 'Private for-profit'
}

# Credential levels
CREDENTIAL_LEVELS = {
    1: 'Undergraduate Certificate or Diploma',
    2: 'Associate\'s Degree',
    3: 'Bachelor\'s Degree',
    4: 'Post-baccalaureate Certificate',
    5: 'Master\'s Degree',
    6: 'Doctoral Degree',
    7: 'First Professional Degree',
    8: 'Graduate/Professional Certificate'
}

# Default budget values (monthly unless specified)
DEFAULT_FOOD_MONTHLY = 400
DEFAULT_UTILITIES_MONTHLY = 150
DEFAULT_TRANSPORT_MONTHLY = 200
DEFAULT_BOOKS_YEARLY = 1200
DEFAULT_MISC_YEARLY = 2000

# Financial calculation defaults
DEFAULT_LOAN_TERM_YEARS = 10
DEFAULT_EARNINGS_GROWTH_RATE = 0.03
DEFAULT_BASELINE_EARNINGS = 35000  # High school graduate baseline
DEFAULT_LOAN_APR = 0.055  # 5.5%
DEFAULT_TAX_RATE = 0.22  # 22%

# Housing type multipliers
HOUSING_MULTIPLIERS = {
    'on_campus': 1.0,
    'off_campus': 1.0,
    'at_home': 0.3  # Significantly reduced costs
}

# Roommate cost reduction (per additional roommate)
ROOMMATE_REDUCTION_RATE = 0.25  # 25% reduction per roommate on housing
MAX_ROOMMATE_DISCOUNT = 0.75  # Maximum 75% discount on housing

# UI slider ranges
MIN_LOAN_APR = 0.03  # 3%
MAX_LOAN_APR = 0.10  # 10%
MIN_TAX_RATE = 0.15  # 15%
MAX_TAX_RATE = 0.35  # 35%

# UI slider steps
LOAN_APR_STEP = 0.005  # 0.5%
TAX_RATE_STEP = 0.01   # 1%

# Default payment rate for debt calculations
DEFAULT_PAYMENT_RATE = 0.10  # 10% of income

# Default graduation rate fallback
DEFAULT_GRADUATION_RATE = 0.5  # 50%

# Comfort index weights
COMFORT_WEIGHTS = {
    'dti': 0.40,  # Debt-to-income ratio (40%)
    'graduation_rate': 0.30,  # Graduation rate (30%)
    'roi': 0.30  # Return on investment (30%)
}

# State cost multipliers for earnings estimation
STATE_COST_MULTIPLIERS = {
    'CA': 1.3, 'NY': 1.25, 'MA': 1.2, 'CT': 1.2, 'NJ': 1.15,
    'MD': 1.15, 'WA': 1.1, 'CO': 1.1, 'VA': 1.05, 'IL': 1.05,
    'TX': 1.0, 'FL': 0.95, 'PA': 0.95, 'OH': 0.9, 'NC': 0.9,
    'GA': 0.9, 'MI': 0.9, 'TN': 0.85, 'IN': 0.85, 'MO': 0.85,
    'KY': 0.8, 'AL': 0.8, 'MS': 0.75, 'WV': 0.75, 'AR': 0.75
}

# Default state multiplier for unknown states
DEFAULT_STATE_MULTIPLIER = 0.9  # 90% of national median

# Housing cost multipliers
TWO_BEDROOM_MULTIPLIER = 1.3  # 2BR costs 30% more than 1BR

# Data version information
DATA_VERSIONS = {
    'college_scorecard': 'Most Recent Cohorts (2024)',
    'hud_safmrs': 'Small Area FMR FY2021-FY2026 (Revised)',
    'bls_cpi': '2024',
    'acs_pums': '2023 1-Year'
}

# SAFMRS Processing Information
SAFMRS_INFO = {
    'data_source': 'HUD Small Area Fair Market Rents (SAFMRS)',
    'url': 'https://www.huduser.gov/portal/datasets/fmr.html',
    'description': 'ZIP code-level fair market rents aggregated to state level',
    'fiscal_years': ['FY2021', 'FY2022', 'FY2023', 'FY2024', 'FY2025', 'FY2026'],
    'aggregation_method': 'Median across all ZIP codes and fiscal years by state',
    'granularity': 'State-level (aggregated from ZIP code)',
    'update_frequency': 'Annual'
}


