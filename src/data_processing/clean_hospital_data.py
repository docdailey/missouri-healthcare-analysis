#!/usr/bin/env python3
"""
Clean hospital data - remove mental health facilities and fix location issues
"""

import pandas as pd
import numpy as np
from pathlib import Path

base_dir = Path(__file__).parent.parent
data_dir = base_dir / "data"

# Load current hospital data
hospital_file = data_dir / "processed" / "missouri_hospitals_geocoded.parquet"
df = pd.read_parquet(hospital_file)

print(f"Original dataset: {len(df)} hospitals")
print("\nHospital types in dataset:")
print(df['Hospital Type'].value_counts())

# Check for mental health facilities
print("\nSearching for mental health/psychiatric facilities...")
mental_health_keywords = ['PSYCHIATRIC', 'MENTAL', 'BEHAVIORAL', 'PSYCH']

for keyword in mental_health_keywords:
    mask = df['Facility Name'].str.upper().str.contains(keyword, na=False)
    if mask.any():
        print(f"\nFacilities with '{keyword}' in name:")
        for idx, row in df[mask].iterrows():
            print(f"  - {row['Facility Name']} ({row['Hospital Type']})")

# Check for Shriners
print("\nSearching for Shriners Hospital...")
shriners_mask = df['Facility Name'].str.upper().str.contains('SHRINERS', na=False)
if shriners_mask.any():
    shriners = df[shriners_mask]
    for idx, row in shriners.iterrows():
        print(f"  Found: {row['Facility Name']}")
        print(f"  Location: {row.get('City/Town', 'Unknown')}, {row.get('County/Parish', 'Unknown')}")
        print(f"  Coordinates: {row.get('latitude', 'N/A')}, {row.get('longitude', 'N/A')}")
        print(f"  Type: {row['Hospital Type']}")

# Remove psychiatric hospitals
psychiatric_mask = df['Hospital Type'] == 'Psychiatric'
if psychiatric_mask.any():
    print(f"\nRemoving {psychiatric_mask.sum()} psychiatric hospitals")
    df_cleaned = df[~psychiatric_mask].copy()
else:
    df_cleaned = df.copy()

# Also remove any facilities with mental/behavioral in the name
mental_name_mask = df_cleaned['Facility Name'].str.upper().str.contains('PSYCHIATRIC|MENTAL|BEHAVIORAL', na=False, regex=True)
if mental_name_mask.any():
    print(f"Removing {mental_name_mask.sum()} additional mental health facilities by name")
    df_cleaned = df_cleaned[~mental_name_mask].copy()

# Fix Shriners location (should be in St. Louis, not Clinton)
shriners_mask = df_cleaned['Facility Name'].str.upper().str.contains('SHRINERS', na=False)
if shriners_mask.any():
    print("\nFixing Shriners Hospital location...")
    # Shriners Hospital for Children - St. Louis actual location
    # Address: 4400 Clayton Ave, St. Louis, MO 63110
    df_cleaned.loc[shriners_mask, 'City/Town'] = 'ST. LOUIS'
    df_cleaned.loc[shriners_mask, 'County/Parish'] = 'ST. LOUIS CITY'
    df_cleaned.loc[shriners_mask, 'latitude'] = 38.6353  # Actual Shriners St. Louis latitude
    df_cleaned.loc[shriners_mask, 'longitude'] = -90.2636  # Actual Shriners St. Louis longitude
    df_cleaned.loc[shriners_mask, 'geocode_quality'] = 'verified'
    print(f"  Updated to St. Louis location (38.6353, -90.2636)")

# Save cleaned data
output_file = data_dir / "processed" / "missouri_hospitals_cleaned.parquet"
df_cleaned.to_parquet(output_file, index=False)
print(f"\nCleaned dataset saved: {output_file}")
print(f"Final dataset: {len(df_cleaned)} hospitals")

# Show final hospital type distribution
print("\nFinal hospital types:")
print(df_cleaned['Hospital Type'].value_counts())

# List any remaining questionable facilities
print("\nRemaining children's hospitals (verify these are general medical):")
children_mask = df_cleaned['Facility Name'].str.upper().str.contains('CHILDREN', na=False)
if children_mask.any():
    for idx, row in df_cleaned[children_mask].iterrows():
        print(f"  - {row['Facility Name']} ({row['Hospital Type']}) in {row.get('City/Town', 'Unknown')}")