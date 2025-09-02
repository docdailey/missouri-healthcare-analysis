# Missouri Healthcare Infrastructure Analysis

A comprehensive geospatial analysis of Missouri's healthcare infrastructure, focusing on hospitals, Rural Health Clinics (RHCs), and Federally Qualified Health Centers (FQHCs). This project identifies service area overlaps, coverage gaps, and opportunities for healthcare system optimization.

## Overview

This repository contains comprehensive data, analysis scripts, and interactive dashboards for Missouri's healthcare infrastructure. The project maps and analyzes hospitals, Rural Health Clinics (RHCs), and Federally Qualified Health Centers (FQHCs) across the state.

### Key Components

- **478 healthcare facilities** mapped and geocoded (105 hospitals, 330 RHCs, 43 FQHCs)
- **Interactive dashboards** for exploring healthcare access patterns
- **Geospatial analysis tools** for service area calculations
- **Data processing pipelines** for CMS and HRSA data integration

## Data Sources

### Primary Datasets
- **CMS Provider Enrollment Data** (April & August 2024): 330 Rural Health Clinics
- **Missouri Hospital Association**: 120 hospitals (105 after geocoding cleanup)
- **HRSA Data Warehouse**: 43 Federally Qualified Health Centers
- **Missouri DHSS**: State health statistics and facility listings

### Data Quality
- 100% geocoding success rate for all facilities
- Fixed 50+ duplicate/overlapping coordinates
- Validated all locations within Missouri boundaries
- Removed 14 incorrectly geocoded psychiatric facilities


## Repository Structure

```
missouri-healthcare-analysis/
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git ignore file
│
├── data/                      # Data directory
│   ├── raw/                   # Original data files
│   ├── processed/             # Cleaned and processed data
│   └── external/              # External reference data
│
├── src/                       # Source code
│   ├── analysis/              # Analysis scripts
│   │   ├── redundancy_analysis.py
│   │   ├── coverage_gaps.py
│   │   └── consolidation_opportunities.py
│   ├── visualization/         # Mapping and visualization
│   │   ├── create_coverage_map.py
│   │   ├── generate_dashboards.py
│   │   └── plot_redundancy.py
│   ├── data_processing/       # Data cleaning and preparation
│   │   ├── geocode_facilities.py
│   │   ├── clean_rhc_data.py
│   │   └── merge_datasets.py
│   └── utils/                 # Utility functions
│       ├── distance_calculations.py
│       └── map_helpers.py
│
├── notebooks/                 # Jupyter notebooks for exploration
│   ├── 01_data_exploration.ipynb
│   ├── 02_redundancy_analysis.ipynb
│   └── 03_optimization_modeling.ipynb
│
├── outputs/                   # Generated outputs
│   ├── maps/                  # Interactive HTML maps
│   ├── reports/               # Analysis reports
│   └── dashboards/            # Interactive dashboards
│
├── docs/                      # Documentation
│   ├── methodology.md         # Analysis methodology
│   ├── data_dictionary.md     # Data field descriptions
│   └── findings_summary.md    # Executive summary
│
└── tests/                     # Unit tests
    ├── test_distance_calc.py
    └── test_geocoding.py
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/missouri-healthcare-analysis.git
cd missouri-healthcare-analysis
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Generate Service Area Analysis
```python
from src.analysis import redundancy_analysis

# Analyze 30-minute service areas
results = redundancy_analysis.analyze_service_areas(
    radius_miles=20,
    facilities_data='data/processed/all_facilities.csv'
)
```

### Create Interactive Map
```python
from src.visualization import create_coverage_map

# Generate comprehensive coverage map
map_html = create_coverage_map.generate_map(
    hospitals='data/processed/hospitals.parquet',
    rhcs='data/processed/rhcs.csv',
    fqhcs='data/processed/fqhcs.csv',
    output_path='outputs/maps/coverage_map.html'
)
```

### Run Complete Analysis Pipeline
```bash
python src/run_full_analysis.py --service-radius 20 --output-dir outputs/
```

## Key Files

- `missouri_healthcare_coverage_map.html` - Main interactive map with all facilities
- `redundancy_analysis_results.json` - Detailed redundancy metrics
- `missouri_rhcs_complete_330_20250831.csv` - Complete RHC dataset
- `missouri_hospitals_properly_geocoded.parquet` - Cleaned hospital data
- `missouri_fqhcs_comprehensive.csv` - FQHC locations and services

## Methodology

### Service Area Definition
- **30-minute drive time** standard for rural healthcare access
- Approximated as **20-mile radius** for rural areas
- Used haversine distance calculation for facility spacing

### Redundancy Scoring
- Counted overlapping facilities within service radius
- Calculated average overlaps per facility type
- Identified clusters with 3+ facilities within 10 miles

### Cost Estimation
- Average RHC operating cost: $2M annually
- Average FQHC operating cost: $5M annually
- Assumed 30% cost reduction potential through consolidation

## Future Enhancements

- [ ] Incorporate actual drive-time data using road networks
- [ ] Add demographic overlays (population density, age distribution)
- [ ] Include quality metrics and patient satisfaction scores
- [ ] Model impact of Rural Emergency Hospital (REH) conversions
- [ ] Add Medicaid/Medicare utilization patterns
- [ ] Create predictive models for facility viability

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions about this analysis or the datasets used, please contact:
- Project Repository: [GitHub Issues](https://github.com/yourusername/missouri-healthcare-analysis/issues)
- Data Sources: Missouri Hospital Association, CMS, HRSA

## Acknowledgments

- Missouri Hospital Association for hospital data
- CMS for Rural Health Clinic enrollment data
- HRSA for FQHC location and service information
- Missouri Department of Health and Senior Services

---

*Analysis completed: September 2025*  
*Last updated: September 2, 2025*