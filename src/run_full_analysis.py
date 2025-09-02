#!/usr/bin/env python3
"""
Main script to run complete Missouri healthcare infrastructure analysis
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import json

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from analysis.redundancy_analysis import analyze_service_redundancy
from visualization.create_coverage_map import create_comprehensive_map


def main():
    parser = argparse.ArgumentParser(description='Missouri Healthcare Infrastructure Analysis')
    parser.add_argument('--service-radius', type=int, default=20,
                       help='Service area radius in miles (default: 20)')
    parser.add_argument('--output-dir', type=str, default='outputs',
                       help='Output directory for results')
    parser.add_argument('--run-redundancy', action='store_true',
                       help='Run redundancy analysis')
    parser.add_argument('--create-maps', action='store_true',
                       help='Create interactive maps')
    parser.add_argument('--all', action='store_true',
                       help='Run all analyses')
    
    args = parser.parse_args()
    
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("="*70)
    print("MISSOURI HEALTHCARE INFRASTRUCTURE ANALYSIS")
    print("="*70)
    
    # Check data files exist
    data_path = Path('data')
    hospital_file = data_path / 'processed' / 'missouri_hospitals_properly_geocoded.parquet'
    rhc_file = data_path / 'raw' / 'missouri_rhcs_complete_330_20250831.csv'
    fqhc_file = data_path / 'external' / 'missouri_fqhcs_comprehensive.csv'
    
    missing_files = []
    if not hospital_file.exists():
        missing_files.append(f"Hospital data: {hospital_file}")
    if not rhc_file.exists():
        missing_files.append(f"RHC data: {rhc_file}")
    if not fqhc_file.exists():
        missing_files.append(f"FQHC data: {fqhc_file}")
    
    if missing_files:
        print("\nERROR: Required data files not found:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nPlease ensure all data files are in the correct locations.")
        return 1
    
    # Run analyses based on arguments
    if args.run_redundancy or args.all:
        print(f"\nRunning redundancy analysis with {args.service_radius}-mile radius...")
        try:
            from analysis import redundancy_analysis
            facilities_df, distances = redundancy_analysis.analyze_service_redundancy()
            print(f"✓ Redundancy analysis complete")
        except Exception as e:
            print(f"✗ Redundancy analysis failed: {e}")
    
    if args.create_maps or args.all:
        print("\nCreating interactive maps...")
        try:
            from visualization import create_coverage_map
            map_file = output_path / 'maps' / 'missouri_healthcare_coverage.html'
            create_coverage_map.create_comprehensive_map(output_file=str(map_file))
            print(f"✓ Map created: {map_file}")
        except Exception as e:
            print(f"✗ Map creation failed: {e}")
    
    # Summary statistics
    print("\n" + "="*70)
    print("ANALYSIS SUMMARY")
    print("="*70)
    
    try:
        # Load and display basic statistics
        hospitals = pd.read_parquet(hospital_file)
        rhcs = pd.read_csv(rhc_file)
        fqhcs = pd.read_csv(fqhc_file)
        
        # Clean data
        hospitals = hospitals[~hospitals['Facility Name'].str.contains(
            'PSYCHIATRIC|MENTAL|SHRINERS|RANKEN', case=False, na=False)]
        rhcs = rhcs[rhcs['latitude'].notna() & rhcs['longitude'].notna()]
        
        print(f"\nFacilities Analyzed:")
        print(f"  • Hospitals: {len(hospitals)}")
        print(f"  • Rural Health Clinics: {len(rhcs)}")
        print(f"  • FQHCs: {len(fqhcs)}")
        print(f"  • Total: {len(hospitals) + len(rhcs) + len(fqhcs)}")
        
        # Geographic coverage
        hospital_cities = hospitals['City/Town'].nunique()
        rhc_cities = rhcs['CITY'].nunique()
        fqhc_cities = fqhcs['City'].nunique()
        
        print(f"\nGeographic Coverage:")
        print(f"  • Hospital cities: {hospital_cities}")
        print(f"  • RHC cities: {rhc_cities}")
        print(f"  • FQHC cities: {fqhc_cities}")
        
    except Exception as e:
        print(f"Could not generate summary statistics: {e}")
    
    print("\n✅ Analysis complete!")
    print(f"Results saved to: {output_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())