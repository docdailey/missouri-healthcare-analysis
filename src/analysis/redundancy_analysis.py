#!/usr/bin/env python3
"""
Analyze redundancy and inefficiency in Missouri healthcare facilities
Based on 30-minute drive time (approximately 20 miles in rural areas)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cdist
import json

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points on Earth in miles"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 3959  # Earth radius in miles
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def analyze_service_redundancy():
    """Analyze overlapping service areas and redundancy"""
    
    print("="*70)
    print("MISSOURI HEALTHCARE SERVICE AREA REDUNDANCY ANALYSIS")
    print("30-Minute Drive Time (≈20 miles radius)")
    print("="*70)
    
    # Load all facility data
    print("\nLoading facility data...")
    
    # Load hospitals
    hospital_file = Path("data/processed/missouri_hospitals_properly_geocoded.parquet")
    if hospital_file.exists():
        hospitals = pd.read_parquet(hospital_file)
        # Filter out psychiatric and problem facilities
        hospitals = hospitals[~hospitals['Facility Name'].str.contains('PSYCHIATRIC|MENTAL|SHRINERS|RANKEN', case=False, na=False)]
    else:
        hospitals = pd.DataFrame()
    
    # Load RHCs
    rhc_file = Path("data/raw/missouri_rhcs_complete_330_20250831.csv")
    if rhc_file.exists():
        rhcs = pd.read_csv(rhc_file)
        # Remove rows with no coordinates (empty rows at the end)
        rhcs = rhcs[rhcs['latitude'].notna() & rhcs['longitude'].notna()]
    else:
        rhcs = pd.DataFrame()
    
    # Load FQHCs
    fqhc_file = Path("data/external/missouri_fqhcs_comprehensive.csv")
    if fqhc_file.exists():
        fqhcs = pd.read_csv(fqhc_file)
    else:
        fqhcs = pd.DataFrame()
    
    print(f"  • Hospitals: {len(hospitals)}")
    print(f"  • RHCs: {len(rhcs)}")
    print(f"  • FQHCs: {len(fqhcs)}")
    
    # Prepare facility datasets with coordinates
    facilities = []
    
    # Add hospitals
    for _, hosp in hospitals.iterrows():
        lat = hosp.get('latitude', 0)
        lon = hosp.get('longitude', 0)
        if lat != 0 and lon != 0:
            facilities.append({
                'name': hosp.get('Facility Name', 'Unknown'),
                'type': 'Hospital',
                'subtype': hosp.get('Hospital Type', 'Unknown'),
                'lat': lat,
                'lon': lon,
                'city': hosp.get('City/Town', 'Unknown')
            })
    
    # Add RHCs
    for _, rhc in rhcs.iterrows():
        lat = rhc.get('Latitude', rhc.get('latitude', 0))
        lon = rhc.get('Longitude', rhc.get('longitude', 0))
        if lat != 0 and lon != 0 and not pd.isna(lat) and not pd.isna(lon):
            name = rhc.get('ORGANIZATION NAME', rhc.get('Clinic Name', 'Unknown'))
            if pd.isna(name) or name == '':
                name = rhc.get('DOING BUSINESS AS NAME', 'Unknown')
            facilities.append({
                'name': name,
                'type': 'RHC',
                'subtype': 'Rural Health Clinic',
                'lat': lat,
                'lon': lon,
                'city': rhc.get('CITY', rhc.get('City', 'Unknown'))
            })
    
    # Add FQHCs
    for _, fqhc in fqhcs.iterrows():
        lat = fqhc.get('Latitude', 0)
        lon = fqhc.get('Longitude', 0)
        if lat != 0 and lon != 0:
            facilities.append({
                'name': fqhc.get('Site_Name', fqhc.get('Organization_Name', 'Unknown')),
                'type': 'FQHC',
                'subtype': fqhc.get('Rural_Urban', 'Unknown'),
                'lat': lat,
                'lon': lon,
                'city': fqhc.get('City', 'Unknown')
            })
    
    facilities_df = pd.DataFrame(facilities)
    print(f"\nTotal facilities with coordinates: {len(facilities_df)}")
    
    # Calculate distance matrix
    print("\nCalculating distance matrix...")
    coords = facilities_df[['lat', 'lon']].values
    n_facilities = len(coords)
    
    # Calculate pairwise distances
    distances = np.zeros((n_facilities, n_facilities))
    for i in range(n_facilities):
        for j in range(i+1, n_facilities):
            dist = haversine_distance(
                coords[i][0], coords[i][1],
                coords[j][0], coords[j][1]
            )
            distances[i][j] = dist
            distances[j][i] = dist
    
    # Define service radius (20 miles for 30-minute drive in rural areas)
    SERVICE_RADIUS = 20
    
    # Analyze overlaps by facility type
    print("\n" + "="*70)
    print("OVERLAP ANALYSIS (Facilities within 20 miles of each other)")
    print("="*70)
    
    # Count overlaps for each facility
    facilities_df['overlaps'] = 0
    facilities_df['overlap_types'] = ''
    
    overlap_details = []
    
    for i in range(n_facilities):
        overlapping = []
        overlap_count = 0
        
        for j in range(n_facilities):
            if i != j and distances[i][j] <= SERVICE_RADIUS:
                overlap_count += 1
                overlapping.append(facilities_df.iloc[j]['type'])
        
        facilities_df.loc[i, 'overlaps'] = overlap_count
        
        if overlap_count > 0:
            type_counts = pd.Series(overlapping).value_counts()
            facilities_df.loc[i, 'overlap_types'] = ', '.join([f"{t}:{c}" for t, c in type_counts.items()])
            
            overlap_details.append({
                'facility': facilities_df.iloc[i]['name'],
                'type': facilities_df.iloc[i]['type'],
                'city': facilities_df.iloc[i]['city'],
                'overlaps': overlap_count,
                'breakdown': dict(type_counts)
            })
    
    # Summary statistics
    print("\n### REDUNDANCY METRICS ###\n")
    
    # By facility type
    for ftype in ['Hospital', 'RHC', 'FQHC']:
        subset = facilities_df[facilities_df['type'] == ftype]
        if len(subset) > 0:
            avg_overlaps = subset['overlaps'].mean()
            max_overlaps = subset['overlaps'].max()
            pct_with_overlap = (subset['overlaps'] > 0).mean() * 100
            
            print(f"{ftype}s:")
            print(f"  • Average overlaps: {avg_overlaps:.1f} facilities")
            print(f"  • Maximum overlaps: {max_overlaps:.0f} facilities")
            print(f"  • % with overlap: {pct_with_overlap:.1f}%")
            print()
    
    # Most redundant locations
    print("\n### HIGHEST REDUNDANCY LOCATIONS ###")
    print("(Most overlapping facilities within 20 miles)\n")
    
    top_redundant = facilities_df.nlargest(15, 'overlaps')
    for _, facility in top_redundant.iterrows():
        print(f"• {facility['name']} ({facility['type']}) - {facility['city']}")
        print(f"  Overlaps with {facility['overlaps']:.0f} facilities: {facility['overlap_types']}")
    
    # Analyze geographic clustering
    print("\n### GEOGRAPHIC CLUSTERING ###\n")
    
    # Group by city and count facilities
    city_counts = facilities_df.groupby('city').agg({
        'name': 'count',
        'type': lambda x: dict(x.value_counts())
    }).rename(columns={'name': 'total_facilities'})
    
    # Cities with most facilities
    top_cities = city_counts.nlargest(10, 'total_facilities')
    
    for city, data in top_cities.iterrows():
        if city != 'Unknown':
            print(f"{city}: {data['total_facilities']} facilities")
            breakdown = data['type']
            for ftype, count in breakdown.items():
                print(f"  • {ftype}: {count}")
    
    # Calculate coverage gaps
    print("\n### EFFICIENCY ANALYSIS ###\n")
    
    # Facilities with no overlaps (potentially serving unique areas)
    isolated = facilities_df[facilities_df['overlaps'] == 0]
    print(f"Facilities with NO overlaps (unique service areas): {len(isolated)}")
    print(f"  • Hospitals: {len(isolated[isolated['type'] == 'Hospital'])}")
    print(f"  • RHCs: {len(isolated[isolated['type'] == 'RHC'])}")
    print(f"  • FQHCs: {len(isolated[isolated['type'] == 'FQHC'])}")
    
    # List the isolated facilities
    print("\n### ISOLATED FACILITIES (No overlaps within 20 miles) ###")
    for _, facility in isolated.iterrows():
        print(f"  • {facility['name']} ({facility['type']}) - {facility['city']}")
    
    # Calculate redundancy score
    total_overlaps = facilities_df['overlaps'].sum() / 2  # Divide by 2 since we count each pair twice
    redundancy_score = total_overlaps / len(facilities_df)
    
    print(f"\nOverall Redundancy Score: {redundancy_score:.2f}")
    print("(Average number of overlapping facilities per location)")
    
    # Estimate potential consolidation
    print("\n### POTENTIAL CONSOLIDATION OPPORTUNITIES ###\n")
    
    # Find clusters of high overlap
    high_overlap = facilities_df[facilities_df['overlaps'] >= 5]
    
    # Group by proximity
    consolidation_opportunities = []
    visited = set()
    
    for i, facility in high_overlap.iterrows():
        if i not in visited:
            cluster = [i]
            visited.add(i)
            
            # Find all facilities within SERVICE_RADIUS
            for j in range(len(facilities_df)):
                if j != i and j not in visited and distances[i][j] <= SERVICE_RADIUS/2:  # Tighter radius for consolidation
                    cluster.append(j)
                    visited.add(j)
            
            if len(cluster) > 2:
                consolidation_opportunities.append(cluster)
    
    print(f"Identified {len(consolidation_opportunities)} potential consolidation clusters")
    print("(Areas with 3+ facilities within 10 miles)\n")
    
    for idx, cluster in enumerate(consolidation_opportunities[:5], 1):
        cluster_facilities = facilities_df.iloc[cluster]
        city = cluster_facilities['city'].mode()[0] if len(cluster_facilities['city'].mode()) > 0 else 'Multiple'
        types = cluster_facilities['type'].value_counts()
        
        print(f"Cluster {idx} - {city} area ({len(cluster)} facilities):")
        for ftype, count in types.items():
            print(f"  • {count} {ftype}(s)")
    
    # Calculate potential savings
    print("\n### ESTIMATED INEFFICIENCY COSTS ###\n")
    
    # Rough estimates
    avg_rhc_cost = 2_000_000  # Annual operating cost estimate
    avg_fqhc_cost = 5_000_000  # Higher due to more services
    
    # Count redundant RHCs and FQHCs (>3 overlaps)
    redundant_rhcs = len(facilities_df[(facilities_df['type'] == 'RHC') & (facilities_df['overlaps'] > 3)])
    redundant_fqhcs = len(facilities_df[(facilities_df['type'] == 'FQHC') & (facilities_df['overlaps'] > 3)])
    
    potential_savings = (redundant_rhcs * avg_rhc_cost * 0.3 +  # Assume 30% cost reduction possible
                        redundant_fqhcs * avg_fqhc_cost * 0.3)
    
    print(f"Redundant RHCs (>3 overlaps): {redundant_rhcs}")
    print(f"Redundant FQHCs (>3 overlaps): {redundant_fqhcs}")
    print(f"Estimated annual inefficiency: ${potential_savings:,.0f}")
    print("(Assuming 30% of costs could be saved through consolidation)")
    
    # Save detailed results
    output_file = Path("analysis/redundancy_analysis_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    results = {
        'summary': {
            'total_facilities': len(facilities_df),
            'hospitals': len(facilities_df[facilities_df['type'] == 'Hospital']),
            'rhcs': len(facilities_df[facilities_df['type'] == 'RHC']),
            'fqhcs': len(facilities_df[facilities_df['type'] == 'FQHC']),
            'redundancy_score': float(redundancy_score),
            'isolated_facilities': len(isolated),
            'consolidation_clusters': len(consolidation_opportunities),
            'estimated_inefficiency': float(potential_savings)
        },
        'top_redundant_facilities': top_redundant[['name', 'type', 'city', 'overlaps']].head(10).to_dict('records'),
        'consolidation_opportunities': len(consolidation_opportunities)
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Detailed results saved to: {output_file}")
    
    return facilities_df, distances

if __name__ == '__main__':
    facilities, distance_matrix = analyze_service_redundancy()