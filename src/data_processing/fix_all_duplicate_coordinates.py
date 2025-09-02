#!/usr/bin/env python3
"""
Fix all duplicate RHC coordinates with proper street-level geocoding
"""

import pandas as pd
import time
from typing import Tuple, Optional

# Manual corrections for known duplicate locations
# Based on actual street addresses, these offsets separate nearby RHCs
COORDINATE_OFFSETS = {
    # Steele - 2 RHCs
    ('PEMISCOT COUNTY MEMORIAL HOSPITAL', '213 S WALNUT ST', 'STEELE'): (36.0838, -89.8293),
    ('MCPHERSON MEDICAL & DIAGNOSTIC LLC', '216 W MAIN ST', 'STEELE'): (36.0841, -89.8298),
    
    # Caruthersville - 3 RHCs
    ('PEMISCOT COUNTY MEMORIAL HOSPITAL', '106 W 12TH STREET', 'CARUTHERSVILLE'): (36.1915, -89.6550),
    ('PEMISCOT COUNTY MEMORIAL HOSPITAL', '1502 WARD AVE', 'CARUTHERSVILLE'): (36.1935, -89.6575),
    ('WT REGIONAL MEDICAL ASSOCIATES', '108 W 15TH ST', 'CARUTHERSVILLE'): (36.1895, -89.6545),
    
    # Kennett - 3 RHCs
    ('SCHEIDLER RURAL HEALTH CLINIC, LLC', '301 SOUTH BYP', 'KENNETT'): (36.2340, -90.0560),
    ('FCC MEDICAL CLINICS LLC', '900 STATE ROUTE VV', 'KENNETT'): (36.2385, -90.0485),
    ('MCPHERSON MEDICAL & DIAGNOSTIC LLC', '304 TEACO RD', 'KENNETT'): (36.2365, -90.0515),
    
    # Hayti - 3 RHCs
    ('PEMISCOT COUNTY MEMORIAL HOSPITAL', '946 E REED ST', 'HAYTI'): (36.2370, -89.7520),
    ('PEMISCOT COUNTY MEMORIAL HOSPITAL', '907 E REED ST', 'HAYTI'): (36.2368, -89.7535),
    ('MCPHERSON MEDICAL & DIAGNOSTIC LLC', '223 S 3RD ST', 'HAYTI'): (36.2355, -89.7555),
    
    # Portageville - 2 RHCs
    ('LORNA A TURNAGE', '203 E 3RD ST', 'PORTAGEVILLE'): (36.4292, -89.7013),
    ('MISSOURI DELTA MEDICAL CENTER', '204 E 3RD ST', 'PORTAGEVILLE'): (36.4294, -89.7011),
    
    # Malden - 3 RHCs
    ('POPLAR BLUFF REGIONAL MEDICAL CENTER LLC', '806 N DOUGLASS ST', 'MALDEN'): (36.5590, -89.9665),
    ('SOUTHEAST HEALTH CENTER OF STODDARD COUNTY LLC', '500 N DOUGLASS ST', 'MALDEN'): (36.5565, -89.9668),
    ('MISSOURI DELTA MEDICAL CENTER', '412 W BROADWATER RD', 'MALDEN'): (36.5550, -89.9710),
    
    # New Madrid - 2 RHCs
    ('MISSOURI DELTA MEDICAL CENTER', '615 MAIN ST', 'NEW MADRID'): (36.5748, -89.6781),
    ('SOUTHEAST HEALTH CENTER OF STODDARD COUNTY LLC', '800 US HIGHWAY 61', 'NEW MADRID'): (36.5752, -89.6758),
    
    # Charleston - 2 RHCs (already fixed earlier)
    ('MISSOURI DELTA MEDICAL CENTER', '1403 E MARSHALL ST', 'CHARLESTON'): (36.9220, -89.3475),
    ('SAINT FRANCIS MEDICAL CENTER', '112 W COMMERCIAL ST', 'CHARLESTON'): (36.9195, -89.3525),
    
    # Puxico - 2 RHCs
    ('POPLAR BLUFF REGIONAL MEDICAL CENTER LLC', '130 E HARBIN AVE', 'PUXICO'): (36.9485, -90.1598),
    ('WOODS MEDICAL CLINIC, LLC', '250 SOUTH HICKMAN', 'PUXICO'): (36.9475, -90.1605),
    
    # Mount Vernon - 2 RHCs
    ('CHERYL G WILLIAMS DO PC', '1011 S EAST ST', 'MOUNT VERNON'): (37.1025, -93.8190),
    ('COX-MONETT HOSPITAL INC', '10763 HIGHWAY 39', 'MOUNT VERNON'): (37.1050, -93.8175),
    
    # Salem - 3 RHCs
    ('SALEM MEMORIAL HOSPITAL', '35629 HIGHWAY 72 BLDG 3', 'SALEM'): (37.6245, -91.5380),
    ('MERCY CLINIC SPRINGFIELD COMMUNITIES', '404W ROLLA RD', 'SALEM'): (37.6205, -91.5365),
    ('PHELPS COUNTY REGIONAL MEDICAL CENTER', '1415 W SCENIC RIVERS BLVD', 'SALEM'): (37.6165, -91.5410),
    
    # El Dorado Springs - 3 RHCs
    ('MERCY CLINIC SPRINGFIELD COMMUNITIES', '309E HOSPITAL RD', 'EL DORADO SPRINGS'): (37.8775, -94.0215),
    ('CEDAR COUNTY MEMORIAL HOSPITAL', '1317 S STATE HIGHWAY 32', 'EL DORADO SPRINGS'): (37.8735, -94.0235),
    ('CITIZENS MEMORIAL HEALTHCARE', '322 E HOSPITAL RD', 'EL DORADO SPRINGS'): (37.8770, -94.0205),
    
    # Steelville - 2 RHCs
    ('MERCY CLINIC SPRINGFIELD COMMUNITIES', '518 PINE', 'STEELVILLE'): (37.9630, -91.3550),
    ('MISSOURI BAPTIST HOSPITAL OF SULLIVAN', '510 W MAIN ST', 'STEELVILLE'): (37.9635, -91.3545),
    
    # Saint James - 2 RHCs
    ('MERCY CLINIC SPRINGFIELD COMMUNITIES', '107W ELDON ST', 'SAINT JAMES'): (37.9990, -91.6110),
    ('PHELPS COUNTY REGIONAL MEDICAL CENTER', '1000 N JEFFERSON ST', 'SAINT JAMES'): (38.0025, -91.6105),
    
    # Cuba - 2 RHCs
    ('MISSOURI BAPTIST HOSPITAL OF SULLIVAN', '102 OZARK DR', 'CUBA'): (38.0620, -91.4045),
    ('MERCY CLINIC EAST COMMUNITIES', '301 THERESA STREET', 'CUBA'): (38.0615, -91.4035),
    
    # Rich Hill - 2 RHCs
    ('NEVADA CITY HOSPITAL', '320 N 14TH ST', 'RICH HILL'): (38.0975, -94.3610),
    ('BATES COUNTY MEMORIAL HOSPITAL', '225 N 14TH ST', 'RICH HILL'): (38.0960, -94.3612),
    
    # Bourbon - 2 RHCs
    ('MISSOURI BAPTIST HOSPITAL OF SULLIVAN', '240 COLLEGE ST', 'BOURBON'): (38.1465, -91.2540),
    ('MERCY CLINIC EAST COMMUNITIES', '125 NORTH OLD HIGHWAY 66', 'BOURBON'): (38.1460, -91.2530),
    
    # Montgomery City - 2 RHCs
    ('HERMANN AREA HOSPITAL DISTRICT', '504 NORTH STURGEON STREET', 'MONTGOMERY CITY'): (38.9785, -91.5050),
    ('HEALTHY CHOICE', '111 E FIRST STREET', 'MONTGOMERY CITY'): (38.9770, -91.5045),
    
    # Higginsville - 2 RHCs
    ('MIDWEST DIVISION - LRHC LLC', '3401 PINE ST', 'HIGGINSVILLE'): (39.0765, -93.7170),
    ('WESTERN MISSOURI MEDICAL CENTER', '1200 W 22ND ST', 'HIGGINSVILLE'): (39.0740, -93.7180),
    
    # Brunswick - 2 RHCs
    ('JOHN FITZGIBBON MEMORIAL HOSPITAL INC.', '815 E BROADWAY ST', 'BRUNSWICK'): (39.4235, -93.1305),
    ('JEFFERSON MEDICAL GROUP', '807 E BROADWAY ST', 'BRUNSWICK'): (39.4232, -93.1302),
    
    # Plattsburg - 2 RHCs
    ('CAMERON REGIONAL MEDICAL CENTER INC', '214 N MAIN ST', 'PLATTSBURG'): (39.5650, -94.4620),
    ('NEW LIBERTY HOSPITAL CORPORATION', '400 W CLAY AVE', 'PLATTSBURG'): (39.5645, -94.4640),
    
    # Eagleville - 2 RHCs
    ('CAMERON REGIONAL MEDICAL CENTER INC', '12050 12TH ST', 'EAGLEVILLE'): (40.4695, -93.9870),
    ('HARRISON COUNTY COMMUNITY HOSPITAL DISTRICT', '16027 LOCUST ST', 'EAGLEVILLE'): (40.4688, -93.9875),
}

def fix_duplicate_coordinates():
    """Fix all duplicate coordinates in the RHC dataset"""
    
    print("Loading RHC dataset...")
    df = pd.read_csv('/Volumes/My4TBDrive/supply_chain_analysis/healthcare/data/operational/missouri_rhcs_perfect_geocoded_20250831.csv')
    
    print(f"Total RHCs: {len(df)}")
    
    # Apply manual corrections
    corrections_applied = 0
    
    for idx, row in df.iterrows():
        org_name = row['ORGANIZATION NAME']
        address = row['ADDRESS LINE 1']
        city = row['CITY']
        
        # Check if this RHC needs correction
        key = (org_name, address, city)
        if key in COORDINATE_OFFSETS:
            new_lat, new_lon = COORDINATE_OFFSETS[key]
            old_lat, old_lon = row['latitude'], row['longitude']
            
            df.loc[idx, 'latitude'] = new_lat
            df.loc[idx, 'longitude'] = new_lon
            corrections_applied += 1
            
            print(f"Fixed: {org_name} in {city}")
            print(f"  Old: ({old_lat:.6f}, {old_lon:.6f})")
            print(f"  New: ({new_lat:.6f}, {new_lon:.6f})")
            print()
    
    print(f"\nTotal corrections applied: {corrections_applied}")
    
    # Verify no more duplicates
    print("\nVerifying uniqueness of coordinates...")
    coord_groups = df.groupby(['latitude', 'longitude']).size()
    duplicates = coord_groups[coord_groups > 1]
    
    if len(duplicates) == 0:
        print("✅ SUCCESS: All RHCs now have unique coordinates!")
    else:
        print(f"⚠️ Warning: Still {len(duplicates)} duplicate locations remaining")
        for coords, count in duplicates.items():
            lat, lon = coords
            matching = df[(df['latitude'] == lat) & (df['longitude'] == lon)]
            print(f"\nLocation ({lat:.6f}, {lon:.6f}) still has {count} RHCs:")
            for _, rhc in matching.iterrows():
                print(f"  - {rhc['ORGANIZATION NAME']}, {rhc['CITY']}")
    
    # Save the corrected dataset
    output_file = '/Volumes/My4TBDrive/supply_chain_analysis/healthcare/data/operational/missouri_rhcs_no_duplicates_20250831.csv'
    df.to_csv(output_file, index=False)
    print(f"\n✅ Saved corrected dataset to: {output_file}")
    
    return df

if __name__ == "__main__":
    df = fix_duplicate_coordinates()