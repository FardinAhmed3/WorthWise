# College ROI Planner

A comprehensive financial analysis tool for college program evaluation, helping students and counselors make informed decisions about higher education investments.

## 🎯 Overview

The College ROI Planner analyzes the true financial outcomes of college programs by computing:

- **Total yearly living costs** (tuition + rent + transport + food + misc)
- **Expected debt at graduation**
- **Projected earnings** (Years 1, 3, and 5)
- **Return on Investment (ROI)**
- **Payback period**
- **Debt-to-income ratio (DTI)**
- **Financial comfort index** (0-100)
- **Graduation rates**

## ✨ Features

### 📊 Single Program Analysis
- Detailed financial breakdown for any college program
- Interactive parameter adjustment (housing, loans, taxes)
- Visual cost breakdown and earnings progression charts

### ⚖️ Program Comparison
- Side-by-side comparison of up to 4 programs
- Comparative visualizations and metrics
- Export results to CSV

### 🗺️ Geographic Analysis
- Regional affordability mapping
- State-level cost and earnings data
- Location-based financial insights

### 📚 Methodology Transparency
- Complete data source documentation
- KPI formula explanations
- Fallback logic for missing data

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/college-roi-planner.git
   cd college-roi-planner
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare data**
   ```bash
   python -m src.data.etl
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:8501`

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t college-roi-planner .
   ```

2. **Run the container**
   ```bash
   docker run -d -p 8501:8501 college-roi-planner
   ```

3. **Access the application**
   Open `http://localhost:8501` in your browser

## 📁 Project Structure

```
college-roi-planner/
├── src/
│   ├── core/           # Financial calculation engine
│   ├── data/           # ETL pipeline and data access
│   └── ui/             # Streamlit page components
├── data/
│   ├── raw/            # Source data files
│   └── processed/      # Processed Parquet files
├── tests/              # Unit tests
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container configuration
└── docker-compose.yml  # Multi-container setup
```

## 📊 Data Sources

- **College Scorecard** - Institution and program data (Most Recent Cohorts 2024)
- **HUD Small Area Fair Market Rents (SAFMRS)** - ZIP code-level housing costs aggregated to state level (FY2021-FY2026)
- **BLS Consumer Price Index** - Inflation adjustments
- **ACS PUMS** - Earnings by major and region (2023 1-Year)

### Data Files Required

Place the following files in the `data/raw/` directory:

1. **College Scorecard Data:**
   - `Most-Recent-Cohorts-Institution.csv`
   - `Most-Recent-Cohorts-Field-of-Study.csv`
   - Available from: https://collegescorecard.ed.gov/data/

2. **HUD Small Area Fair Market Rents (SAFMRS):**
   - `fy2021_safmrs_revised.xlsx`
   - `fy2022_safmrs_revised.xlsx`
   - `fy2023_safmrs_revised.xlsx`
   - `fy2024_safmrs_revised.xlsx`
   - `fy2025_safmrs_revised.xlsx`
   - `fy2026_safmrs_revised.xlsx`
   - Available from: https://www.huduser.gov/portal/datasets/fmr.html
   - Note: SAFMRS provide ZIP code-level rent data for more accurate housing cost estimates

3. **BLS CPI Data:**
   - `cu.data.1.AllItems`
   - Available from: https://www.bls.gov/cpi/data.htm

4. **ACS PUMS Data:**
   - `acs_pums.json`
   - Available from: https://www.census.gov/programs-surveys/acs/microdata.html

**Note:** The ETL pipeline will automatically create default fallback data for any missing files.

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.11, Pandas, NumPy
- **Visualization**: Plotly, PyDeck
- **Storage**: Parquet files with DuckDB queries
- **Deployment**: Docker

## 📈 Performance

- **Cold start**: ≤ 3 seconds
- **KPI updates**: < 300ms
- **Map rendering**: ≤ 3 seconds
- **Data processing**: Optimized with Parquet + DuckDB

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

## 📝 Usage

1. **Select Institution & Program**: Choose from dropdown menus
2. **Adjust Parameters**: Modify housing, loan, and tax settings
3. **View Results**: Analyze KPIs and visualizations
4. **Compare Programs**: Use the Compare page for side-by-side analysis
5. **Export Data**: Download results as CSV

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For questions or issues:
- Open an issue on GitHub
- Check the [Methodology](http://localhost:8501/Methodology) page for detailed explanations
- Review the [PRD.md](PRD.md) for complete project requirements

## 🎓 About

Built to help students make informed decisions about their educational investments by providing transparent, data-driven financial analysis of college programs.

---

**Version**: 1.0.0  
**Status**: Production Ready ✅