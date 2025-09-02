#!/usr/bin/env python3
"""
Download and process Missouri FQHC (Federally Qualified Health Center) data
"""

import pandas as pd
import requests
import json
from pathlib import Path


def download_hrsa_fqhc_data():
    """Download FQHC data from HRSA or other sources"""

    print("Downloading Missouri FQHC data...")

    # Try HRSA Data Warehouse API
    # HRSA provides health center data through their data warehouse
    base_url = "https://data.hrsa.gov/api/v1/data"

    # Create data directory
    data_dir = Path("data/fqhc")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Try to get FQHC data
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    # HRSA Health Center Program data endpoint
    # Note: HRSA often requires specific API keys or uses different endpoints
    # We'll try multiple approaches

    print("Attempting to download from HRSA data sources...")

    # Approach 1: Try direct HRSA API
    try:
        # HRSA Find a Health Center API
        hrsa_url = "https://findahealthcenter.hrsa.gov/api/v0/centers/search"
        params = {
            "state": "MO",
            "radius": 500,  # Get all in state
            "lat": 38.5,  # Missouri center
            "lon": -92.5,
            "pageNumber": 1,
            "pageSize": 500,
        }

        response = requests.get(hrsa_url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("Successfully downloaded FQHC data")

            # Save raw data
            with open(data_dir / "hrsa_fqhc_raw.json", "w") as f:
                json.dump(data, f, indent=2)

            return process_hrsa_data(data)
    except Exception as e:
        print(f"HRSA API error: {e}")

    # Approach 2: Create template for manual data entry
    print("\nCreating FQHC data template for manual collection...")

    # Based on known Missouri FQHCs
    template_data = {
        "Organization_Name": [
            "ACCESS Family Care",
            "Affinia Healthcare",
            "Betty Jean Kerr People's Health Centers",
            "CareSTL Health",
            "Central Ozarks Medical Center",
            "Clark Community Mental Health Center",
            "Compass Health Network",
            "Family Health Center of Missouri",
            "Freeman Health System",
            "Grace Hill Health Centers",
            "Jordan Valley Community Health Center",
            "Myrtle Hilliard Davis Comprehensive Health Centers",
            "Samuel U. Rodgers Health Center",
            "Swope Health Services",
        ],
        "Type": ["FQHC"] * 14,
        "City": [
            "Neosho",
            "St. Louis",
            "St. Louis",
            "St. Louis",
            "Richland",
            "Nevada",
            "Columbia",
            "Columbia",
            "Joplin",
            "St. Louis",
            "Springfield",
            "St. Louis",
            "Kansas City",
            "Kansas City",
        ],
        "State": ["MO"] * 14,
        "Rural_Urban": [
            "Rural",
            "Urban",
            "Urban",
            "Urban",
            "Rural",
            "Rural",
            "Urban",
            "Urban",
            "Urban",
            "Urban",
            "Urban",
            "Urban",
            "Urban",
            "Urban",
        ],
        "Address": [""] * 14,
        "ZIP": [""] * 14,
        "Phone": [""] * 14,
        "Website": [""] * 14,
        "Services": ["Primary Care, Dental, Behavioral Health"] * 14,
        "Latitude": [0.0] * 14,
        "Longitude": [0.0] * 14,
    }

    template_df = pd.DataFrame(template_data)
    template_file = data_dir / "missouri_fqhc_template.csv"
    template_df.to_csv(template_file, index=False)
    print(f"Template saved to: {template_file}")

    return template_df


def process_hrsa_data(data):
    """Process HRSA JSON data into DataFrame"""

    if isinstance(data, dict) and "results" in data:
        centers = data["results"]
    else:
        centers = data

    fqhc_list = []
    for center in centers:
        if isinstance(center, dict):
            fqhc = {
                "Organization_Name": center.get("name", ""),
                "Type": "FQHC",
                "Address": center.get("address", {}).get("line1", ""),
                "City": center.get("address", {}).get("city", ""),
                "State": center.get("address", {}).get("stateCode", "MO"),
                "ZIP": center.get("address", {}).get("postalCode", ""),
                "Phone": center.get("telephone", ""),
                "Website": center.get("website", ""),
                "Latitude": center.get("geolocation", {}).get("latitude", 0),
                "Longitude": center.get("geolocation", {}).get("longitude", 0),
                "Services": ", ".join(center.get("services", []))
                if "services" in center
                else "",
            }
            fqhc_list.append(fqhc)

    df = pd.DataFrame(fqhc_list)
    return df


def geocode_fqhcs(df):
    """Geocode FQHCs that don't have coordinates"""

    print("\nGeocoding FQHCs without coordinates...")

    # Missouri city coordinates for basic geocoding
    city_coords = {
        "NEOSHO": (36.8689, -94.3680),
        "ST. LOUIS": (38.6270, -90.1994),
        "SAINT LOUIS": (38.6270, -90.1994),
        "RICHLAND": (37.8567, -92.4043),
        "NEVADA": (37.8392, -94.3547),
        "COLUMBIA": (38.9517, -92.3341),
        "JOPLIN": (37.0842, -94.5133),
        "SPRINGFIELD": (37.2090, -93.2923),
        "KANSAS CITY": (39.0997, -94.5786),
        "INDEPENDENCE": (39.0911, -94.4155),
        "JEFFERSON CITY": (38.5767, -92.1735),
        "CAPE GIRARDEAU": (37.3058, -89.5181),
        "SEDALIA": (38.7045, -93.2283),
        "ROLLA": (37.9486, -91.7715),
        "FARMINGTON": (37.7806, -90.4218),
        "POPLAR BLUFF": (36.7570, -90.3929),
        "KIRKSVILLE": (40.1948, -92.5832),
        "WARRENSBURG": (38.7628, -93.7360),
        "WEST PLAINS": (36.7323, -91.8524),
        "MARSHFIELD": (37.3387, -92.9071),
    }

    for idx, row in df.iterrows():
        if row["Latitude"] == 0 or pd.isna(row["Latitude"]):
            city = str(row["City"]).upper()
            if city in city_coords:
                df.at[idx, "Latitude"] = city_coords[city][0]
                df.at[idx, "Longitude"] = city_coords[city][1]
                print(f"  Geocoded {row['Organization_Name']} in {city}")

    return df


def classify_rural_urban(df):
    """Classify FQHCs as rural or urban based on location"""

    print("\nClassifying FQHCs as rural or urban...")

    # Urban areas in Missouri
    urban_cities = [
        "ST. LOUIS",
        "SAINT LOUIS",
        "KANSAS CITY",
        "SPRINGFIELD",
        "COLUMBIA",
        "INDEPENDENCE",
        "LEE'S SUMMIT",
        "O'FALLON",
        "ST. JOSEPH",
        "ST. CHARLES",
        "BLUE SPRINGS",
        "FLORISSANT",
        "JOPLIN",
        "CHESTERFIELD",
        "JEFFERSON CITY",
        "CAPE GIRARDEAU",
    ]

    # Add rural/urban classification if not present
    if "Rural_Urban" not in df.columns:
        df["Rural_Urban"] = "Rural"  # Default to rural

    for idx, row in df.iterrows():
        city = str(row["City"]).upper()
        if any(urban in city for urban in urban_cities):
            df.at[idx, "Rural_Urban"] = "Urban"
        else:
            df.at[idx, "Rural_Urban"] = "Rural"

    return df


def main():
    """Main function to download and process FQHC data"""

    print("=" * 60)
    print("MISSOURI FQHC DATA COLLECTION")
    print("=" * 60)

    # Download data
    df = download_hrsa_fqhc_data()

    # Geocode if needed
    df = geocode_fqhcs(df)

    # Classify rural/urban
    df = classify_rural_urban(df)

    # Save processed data
    output_file = Path("data/fqhc/missouri_fqhcs_processed.csv")
    df.to_csv(output_file, index=False)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total FQHCs collected: {len(df)}")
    print(f"Rural FQHCs: {len(df[df['Rural_Urban'] == 'Rural'])}")
    print(f"Urban FQHCs: {len(df[df['Rural_Urban'] == 'Urban'])}")
    print(f"With coordinates: {len(df[df['Latitude'] != 0])}")
    print(f"\nData saved to: {output_file}")

    return df


if __name__ == "__main__":
    main()
