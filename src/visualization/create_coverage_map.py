#!/usr/bin/env python3
"""
Create Interactive Map of Missouri Hospitals and RHCs with Coverage Circles
Shows both hospitals and Rural Health Clinics with toggleable coverage areas
"""

import pandas as pd
import folium
from folium import plugins
import numpy as np
from pathlib import Path
import json

def create_coverage_circles(lat, lon, radius_miles, color='blue', fill_opacity=0.1):
    """Create coverage circle for a facility
    
    Args:
        lat: Latitude
        lon: Longitude
        radius_miles: Radius in miles
        color: Circle color
        fill_opacity: Fill opacity (0-1)
    """
    # Convert miles to meters (1 mile = 1609.34 meters)
    radius_meters = radius_miles * 1609.34
    
    return folium.Circle(
        location=[lat, lon],
        radius=radius_meters,
        color=color,
        fill=True,
        fillColor=color,
        fillOpacity=fill_opacity,
        weight=1,
        opacity=0.3
    )

def create_comprehensive_coverage_map():
    """Create map with hospitals, RHCs, and coverage circles"""
    
    print("="*60)
    print("CREATING MISSOURI HEALTHCARE COVERAGE MAP")
    print("="*60)
    
    # Load hospital data - use the properly geocoded parquet file
    hospital_file = Path("data/processed/missouri_hospitals_properly_geocoded.parquet")
    if hospital_file.exists():
        hospitals = pd.read_parquet(hospital_file)
        print(f"  Using properly geocoded parquet file")
    else:
        # Fallback to CSV (has incorrect geocoding)
        hospital_file = Path("data/processed/missouri_hospitals_geocoded.csv")
        hospitals = pd.read_csv(hospital_file)
        hospitals = hospitals[hospitals['State'] == 'MO'].copy()
        print(f"  WARNING: Using CSV with geocoding issues")
    print(f"✓ Loaded {len(hospitals)} Missouri hospitals")
    
    # Load RHC data (complete 330 dataset)
    rhc_file = Path("data/operational/missouri_rhcs_complete_330_20250831.csv")
    if not rhc_file.exists():
        rhc_file = Path("data/operational/missouri_rhcs_final_corrected_20250831.csv")
    rhcs = pd.read_csv(rhc_file)
    print(f"✓ Loaded {len(rhcs)} Missouri RHCs")
    
    # Load FQHC data
    fqhc_file = Path("data/fqhc/missouri_fqhcs_comprehensive.csv")
    if fqhc_file.exists():
        fqhcs = pd.read_csv(fqhc_file)
        print(f"✓ Loaded {len(fqhcs)} Missouri FQHC sites")
    else:
        fqhcs = pd.DataFrame()  # Empty if not found
        print("  No FQHC data found")
    
    # Create base map centered on Missouri
    missouri_center = [38.5, -92.5]
    m = folium.Map(
        location=missouri_center,
        zoom_start=7,
        tiles='OpenStreetMap',
        prefer_canvas=True
    )
    
    # Add alternative tile layers
    folium.TileLayer('CartoDB positron', name='Light Map').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='Dark Map').add_to(m)
    
    # Create feature groups for different layers
    hospital_group = folium.FeatureGroup(name='🏥 Hospitals', show=True)
    rhc_group = folium.FeatureGroup(name='🏘️ Rural Health Clinics', show=True)
    fqhc_group = folium.FeatureGroup(name='🏢 FQHCs (Fed. Qualified)', show=True)
    
    # Coverage circle groups (initially hidden)
    coverage_15min = folium.FeatureGroup(name='⭕ 15-min Coverage (10 mi)', show=False)
    coverage_30min = folium.FeatureGroup(name='⭕ 30-min Coverage (20 mi)', show=False)
    coverage_45min = folium.FeatureGroup(name='⭕ 45-min Coverage (30 mi)', show=False)
    
    # Add hospitals to map (excluding psychiatric facilities)
    print("\nAdding hospitals (excluding psychiatric facilities)...")
    hospital_types = {
        'Critical Access Hospitals': '🏥',
        'Acute Care Hospitals': '🏨',
        'Childrens': '👶'
    }
    
    skipped_psychiatric = 0
    for idx, hospital in hospitals.iterrows():
        # Handle different column names between CSV and parquet
        hosp_type = hospital.get('Hospital Type', hospital.get('hospital_type', 'Unknown'))
        facility_name = str(hospital.get('Facility Name', hospital.get('name', ''))).upper()
        
        # Skip psychiatric hospitals and Shriners due to geolocation issues
        if ('Psychiatric' in str(hosp_type) or 
            'Mental' in facility_name or 
            'SHRINERS' in facility_name or
            'RANKEN JORDAN' in facility_name):  # Also skip Ranken Jordan as you mentioned
            skipped_psychiatric += 1
            continue
        
        if 'Critical Access' in hosp_type:
            icon_color = 'red'
            icon = 'plus-sign'
            marker_color = 'red'
        elif 'Children' in hosp_type:
            icon_color = 'pink'
            icon = 'child'
            marker_color = 'pink'
        else:
            icon_color = 'blue'
            icon = 'hospital-o'
            marker_color = 'blue'
        
        # Get coordinates
        lat = hospital.get('latitude', hospital.get('lat', None))
        lon = hospital.get('longitude', hospital.get('lon', None))
        
        if pd.notna(lat) and pd.notna(lon):
            # Create popup text (handle different column names)
            name = hospital.get('Facility Name', hospital.get('name', 'Unknown'))
            city = hospital.get('City/Town', hospital.get('city', 'Unknown'))
            county = hospital.get('County/Parish', hospital.get('county', 'N/A'))
            emergency = hospital.get('Emergency Services', hospital.get('emergency_services', 'N/A'))
            ownership = hospital.get('Hospital Ownership', hospital.get('ownership', 'N/A'))
            rating = hospital.get('Hospital overall rating', hospital.get('overall_rating', 'N/A'))
            
            popup_text = f"""
            <div style='width: 250px'>
                <h4>{name}</h4>
                <b>Type:</b> {hosp_type}<br>
                <b>City:</b> {city}<br>
                <b>County:</b> {county}<br>
                <b>Emergency:</b> {emergency}<br>
                <b>Ownership:</b> {ownership}<br>
                <b>Overall Rating:</b> {rating}<br>
            </div>
            """
            
            # Add hospital marker
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_text, max_width=250),
                tooltip=f"{name} ({hosp_type})",
                icon=folium.Icon(color=marker_color, icon=icon, prefix='fa')
            ).add_to(hospital_group)
            
            # Add coverage circles for hospitals
            # 15-minute drive (~10 miles in rural areas)
            create_coverage_circles(lat, lon, 10, color=marker_color, fill_opacity=0.05).add_to(coverage_15min)
            
            # 30-minute drive (~20 miles in rural areas)
            create_coverage_circles(lat, lon, 20, color=marker_color, fill_opacity=0.05).add_to(coverage_30min)
            
            # 45-minute drive (~30 miles in rural areas)
            create_coverage_circles(lat, lon, 30, color=marker_color, fill_opacity=0.05).add_to(coverage_45min)
    
    # Count hospitals actually added
    hospitals_added = len(hospitals) - skipped_psychiatric
    print(f"  Added {hospitals_added} hospitals with valid coordinates")
    print(f"  Skipped {skipped_psychiatric} facilities with incorrect geolocation (psychiatric/Shriners)")
    
    # Add RHCs to map
    print("\nAdding Rural Health Clinics...")
    
    # Define health system colors for RHCs
    health_system_colors = {
        'MERCY': '#00897b',
        'COXHEALTH': '#1976d2',
        'CITIZENS MEMORIAL': '#d32f2f',
        'HANNIBAL': '#7b1fa2',
        'GOLDEN VALLEY': '#f57c00',
        'Noble Health': '#689f38',
        'Cameron Regional': '#5d4037',
        'Independent': '#616161'
    }
    
    rhc_count = 0
    for idx, rhc in rhcs.iterrows():
        # Get coordinates - try multiple column names
        lat = rhc.get('Latitude', rhc.get('latitude', rhc.get('lat', None)))
        lon = rhc.get('Longitude', rhc.get('longitude', rhc.get('lon', None)))
        
        if pd.notna(lat) and pd.notna(lon):
            # Get health system for color
            health_system = rhc.get('Health_System', rhc.get('Health System', 'Independent'))
            
            # Determine color based on health system
            marker_color = 'green'  # Default for RHCs
            for system, color in health_system_colors.items():
                if system.upper() in str(health_system).upper():
                    marker_color = 'darkgreen'
                    break
            
            # Get clinic name - check all possible column names
            clinic_name = (rhc.get('DOING BUSINESS AS NAME') or 
                          rhc.get('ORGANIZATION NAME') or
                          rhc.get('Clinic Name') or 
                          rhc.get('Provider_Name') or 
                          'Unknown RHC')
            
            city = rhc.get('CITY') or rhc.get('City') or rhc.get('Provider_City') or 'Unknown'
            address = rhc.get('ADDRESS LINE 1') or rhc.get('Address') or rhc.get('Provider_Address') or 'N/A'
            state = rhc.get('STATE') or rhc.get('State') or 'MO'
            zip_code = rhc.get('ZIP CODE') or rhc.get('Zip') or ''
            county = rhc.get('County') or rhc.get('COUNTY') or 'N/A'
            npi = rhc.get('NPI') or rhc.get('Provider_NPI') or 'N/A'
            ccn = rhc.get('CCN') or 'N/A'
            
            # Create popup text with actual RHC data
            popup_text = f"""
            <div style='width: 300px'>
                <h4 style='margin-bottom: 5px;'>{clinic_name}</h4>
                <p style='margin: 2px 0;'><b>Type:</b> Rural Health Clinic</p>
                <p style='margin: 2px 0;'><b>Address:</b> {address}</p>
                <p style='margin: 2px 0;'><b>City:</b> {city}, {state} {zip_code}</p>
                <p style='margin: 2px 0;'><b>County:</b> {county}</p>
                <p style='margin: 2px 0;'><b>Health System:</b> {health_system}</p>
                <p style='margin: 2px 0;'><b>NPI:</b> {npi}</p>
                <p style='margin: 2px 0;'><b>CCN:</b> {ccn}</p>
                <p style='margin: 2px 0;'><b>Est. Annual Visits:</b> {rhc.get('Estimated_Annual_Visits', 'N/A')}</p>
                <p style='margin: 2px 0;'><b>Volume Category:</b> {rhc.get('Volume_Category', 'N/A')}</p>
            </div>
            """
            
            # Add RHC marker - use regular marker with green icon for better clickability
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_text, max_width=250),
                tooltip=f"{clinic_name} (RHC)",
                icon=folium.Icon(color='green', icon='medkit', prefix='fa', icon_color='white')
            ).add_to(rhc_group)
            
            # Add smaller coverage circles for RHCs
            # 15-minute drive (~10 miles)
            create_coverage_circles(lat, lon, 10, color='green', fill_opacity=0.03).add_to(coverage_15min)
            
            # 30-minute drive (~20 miles)
            create_coverage_circles(lat, lon, 20, color='green', fill_opacity=0.03).add_to(coverage_30min)
            
            # 45-minute drive (~30 miles)
            create_coverage_circles(lat, lon, 30, color='green', fill_opacity=0.03).add_to(coverage_45min)
            
            rhc_count += 1
    
    print(f"  Added {rhc_count} RHCs with coordinates")
    
    # Add FQHCs to map
    if len(fqhcs) > 0:
        print("\nAdding Federally Qualified Health Centers...")
        fqhc_count = 0
        
        for idx, fqhc in fqhcs.iterrows():
            lat = fqhc.get('Latitude', 0)
            lon = fqhc.get('Longitude', 0)
            
            if lat != 0 and lon != 0:
                # Determine marker color based on rural/urban
                rural_urban = fqhc.get('Rural_Urban', 'Unknown')
                if rural_urban == 'Rural':
                    marker_color = 'orange'
                    icon_name = 'home'
                else:
                    marker_color = 'darkblue'
                    icon_name = 'building'
                
                # Create popup text
                popup_text = f"""
                <div style='width: 300px'>
                    <h4 style='margin-bottom: 5px;'>{fqhc.get('Site_Name', fqhc.get('Organization_Name', 'Unknown'))}</h4>
                    <p style='margin: 2px 0;'><b>Type:</b> Federally Qualified Health Center</p>
                    <p style='margin: 2px 0;'><b>Organization:</b> {fqhc.get('Organization_Name', 'N/A')}</p>
                    <p style='margin: 2px 0;'><b>Address:</b> {fqhc.get('Address', 'N/A')}</p>
                    <p style='margin: 2px 0;'><b>City:</b> {fqhc.get('City', 'N/A')}, MO {fqhc.get('ZIP', '')}</p>
                    <p style='margin: 2px 0;'><b>County:</b> {fqhc.get('County', 'N/A')}</p>
                    <p style='margin: 2px 0;'><b>Setting:</b> {rural_urban}</p>
                    <p style='margin: 2px 0;'><b>Services:</b> {fqhc.get('Services', 'Primary Care')}</p>
                </div>
                """
                
                # Add FQHC marker
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=f"{fqhc.get('Site_Name', 'FQHC')} ({rural_urban})",
                    icon=folium.Icon(color=marker_color, icon=icon_name, prefix='fa', icon_color='white')
                ).add_to(fqhc_group)
                
                # Add coverage circles for FQHCs
                # 15-minute drive (~10 miles)
                create_coverage_circles(lat, lon, 10, color='darkblue', fill_opacity=0.03).add_to(coverage_15min)
                
                # 30-minute drive (~20 miles)
                create_coverage_circles(lat, lon, 20, color='darkblue', fill_opacity=0.03).add_to(coverage_30min)
                
                # 45-minute drive (~30 miles)
                create_coverage_circles(lat, lon, 30, color='darkblue', fill_opacity=0.03).add_to(coverage_45min)
                
                fqhc_count += 1
        
        print(f"  Added {fqhc_count} FQHC sites with coordinates")
        print(f"    - Rural FQHCs: {len(fqhcs[fqhcs['Rural_Urban'] == 'Rural'])}")
        print(f"    - Urban FQHCs: {len(fqhcs[fqhcs['Rural_Urban'] == 'Urban'])}")
    
    # Add all groups to map
    hospital_group.add_to(m)
    rhc_group.add_to(m)
    fqhc_group.add_to(m)
    coverage_15min.add_to(m)
    coverage_30min.add_to(m)
    coverage_45min.add_to(m)
    
    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 280px; height: auto; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius: 10px; padding: 10px">
        
        <h4 style="margin-top:0; margin-bottom:10px;">Missouri Healthcare Facilities</h4>
        
        <p style="margin: 5px 0;"><b>Hospitals:</b></p>
        <p style="margin: 2px 0;">🔴 Critical Access Hospitals</p>
        <p style="margin: 2px 0;">🔵 Acute Care Hospitals</p>
        <p style="margin: 2px 0;">🩷 Children's Hospitals</p>
        
        <p style="margin: 10px 0 5px 0;"><b>Rural Health Clinics:</b></p>
        <p style="margin: 2px 0;">🟢 All RHCs (330 total)</p>
        
        <p style="margin: 10px 0 5px 0;"><b>FQHCs (Federally Qualified):</b></p>
        <p style="margin: 2px 0;">🟠 Rural FQHCs</p>
        <p style="margin: 2px 0;">🔵 Urban FQHCs</p>
        
        <p style="margin: 10px 0 5px 0;"><b>Coverage Areas:</b></p>
        <p style="margin: 2px 0;">⭕ Toggle layers to show coverage</p>
        <p style="margin: 2px 0;">• 15 min = ~10 miles</p>
        <p style="margin: 2px 0;">• 30 min = ~20 miles</p>
        <p style="margin: 2px 0;">• 45 min = ~30 miles</p>
        
        <p style="margin: 10px 0 0 0;"><i>Click markers for details</i></p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add fullscreen button
    plugins.Fullscreen().add_to(m)
    
    # Add search functionality
    plugins.Search(
        layer=hospital_group,
        search_label='Facility Name',
        search_zoom=12,
        start_record=0,
        placeholder='Search Hospitals...'
    ).add_to(m)
    
    # Save map
    output_dir = Path("analysis/optimization/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "missouri_healthcare_coverage_map.html"
    
    m.save(str(output_file))
    
    print("\n" + "="*60)
    print("MAP CREATION COMPLETE")
    print("="*60)
    
    print(f"""
📊 Final Statistics:
  • Total Hospitals: {len(hospitals)}
    - Critical Access: {hospitals['Hospital Type'].str.contains('Critical Access', na=False).sum()}
    - Acute Care: {hospitals['Hospital Type'].str.contains('Acute Care', na=False).sum()}
    - Other Types: {len(hospitals) - hospitals['Hospital Type'].str.contains('Critical Access|Acute Care', na=False).sum()}
  
  • Total RHCs: {len(rhcs)}
    - With coordinates: {rhc_count}
  
  • Total FQHCs: {len(fqhcs) if len(fqhcs) > 0 else 'Not loaded'}
    - Rural: {len(fqhcs[fqhcs['Rural_Urban'] == 'Rural']) if len(fqhcs) > 0 else 0}
    - Urban: {len(fqhcs[fqhcs['Rural_Urban'] == 'Urban']) if len(fqhcs) > 0 else 0}
  
  • Coverage Layers:
    - 15-minute drive time (~10 miles)
    - 30-minute drive time (~20 miles)  
    - 45-minute drive time (~30 miles)

✅ Map saved to: {output_file}
📍 Open in browser: file://{output_file.absolute()}

💡 Tips:
  • Use layer control (top right) to toggle hospitals, RHCs, and coverage circles
  • Click on any marker for detailed information
  • Use search box to find specific hospitals
  • Toggle base maps for different views
""")

if __name__ == '__main__':
    create_comprehensive_coverage_map()