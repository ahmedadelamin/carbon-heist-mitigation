import pandas as pd
import numpy as np

def clean_ll97_data(raw_data_path, output_path):
    print("Loading raw data...")
    df = pd.read_excel(raw_data_path, sheet_name=0)
    
    print("Applying Power Query cleaning steps...")
    
    # 1. Replace "Not Available" with NaN
    df = df.replace("Not Available", np.nan)
    
    # Enforce Numeric Types (Matching PQ's Change Type Step)
    numeric_cols = [
        "Property GFA - Calculated (Buildings and Parking) (ft²)",
        "Property GFA - Calculated (Buildings) (ft²)",
        "Property GFA - Calculated (Parking) (ft²)",
        "ENERGY STAR Score", "National Median ENERGY STAR Score", "Target ENERGY STAR Score",
        "Site EUI (kBtu/ft²)", "Site Energy Use (kBtu)", "Source Energy Use (kBtu)", 
        "Source EUI (kBtu/ft²)", "eGRID Output Emissions Rate (kgCO2e/MBtu)",
        "Total GHG Emissions (Metric Tons CO2e)", "Total GHG Emissions Intensity (kgCO2e/ft²)",
        "Net Emissions (Metric Tons CO2e)", "National Median Total GHG Emissions (Metric Tons CO2e)",
        "Fuel Oil #1 Use (kBtu)", "Fuel Oil #2 Use (kBtu)", "Fuel Oil #4 Use (kBtu)",
        "Fuel Oil #5 & 6 Use (kBtu)", "District Steam Use (kBtu)", "Diesel #2 Use (kBtu)",
        "Propane Use (kBtu)", "District Hot Water Use (kBtu)", "District Chilled Water Use (kBtu)",
        "Natural Gas Use (kBtu)", "Electricity Use - Grid Purchase (kBtu)"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 2. Standardize Alerts ("OK" to "Ok") and Fix French Translation
    alert_cols = [c for c in df.columns if "Alert" in c]
    for col in alert_cols:
        df[col] = df[col].replace("OK", "Ok")
        
    if 'Alert - Water Meter has less than 12 full calendar months of data' in df.columns:
        df['Alert - Water Meter has less than 12 full calendar months of data'] = df['Alert - Water Meter has less than 12 full calendar months of data'].replace(
            "Non vérifié (consulter les enjeux possibles)", "Unable to Check (not enough data)"
        )
        
    # 3. Formatting Text Columns (Construction Status, City, Parent Property)
    if 'Construction Status' in df.columns:
        df['Construction Status'] = df['Construction Status'].replace("Existante", "Existing")
        
    if 'City' in df.columns:
        city_replacements = {
            "Ny": "New York", "New York City": "New York", "Quuens": "Queens", "The Bronx": "Bronx",
            "Queens,": "Queens", "Quens": "Queens", "Queen": "Queens", "New York,": "New York",
            "New Yok": "New York", "New Yrk": "New York", "New Yorkc": "New York", "beonx": "Bronx", "bronx": "Bronx"
        }
        df['City'] = df['City'].replace(city_replacements)
        df['City'] = df['City'].str.title().str.strip()
        
    for col in ['Parent Property Id', 'Parent Property Name']:
        if col in df.columns:
            df[col] = df[col].replace("Not Applicable: Standalone Property", "Standalone").str.strip()
            
    # Trimming String Values
    trim_cols = ["Property Name", "Primary Property Type - Portfolio Manager-Calculated", "Borough", "Metered Areas (Energy)", "Metered Areas (Water)"]
    for col in trim_cols:
        if col in df.columns:
            df[col] = df[col].str.strip()
            
    # 4. Data Engineering: Custom Columns Calculation
    if 'Year Built' in df.columns:
        df['Year Built'] = pd.to_numeric(df['Year Built'], errors='coerce')
        df = df[(df['Year Built'] >= 1800) & (df['Year Built'] <= 2021)]
        df['Building Age'] = 2021 - df['Year Built']
        df['Decade Built'] = (np.floor(df['Year Built'] / 10) * 10).astype(int).astype(str) + "s"
    
    if 'Borough' in df.columns:
        df['Borough'] = df['Borough'].str.title()
        
    ghg_col = "Total GHG Emissions (Metric Tons CO2e)"
    gfa_col = "Property GFA - Calculated (Buildings and Parking) (ft²)"
    if ghg_col in df.columns:
        df['Base LL97 Penalty'] = df[ghg_col] * 268
    if gfa_col in df.columns:
        df['Base Penalty $/ft²'] = df['Base LL97 Penalty'] / df[gfa_col]
        
    # 5. Filtering Target Data
    if 'Construction Status' in df.columns:
        df = df[df['Construction Status'] != "Test"]
        
    if gfa_col in df.columns:
        df = df[df[gfa_col] >= 50000]
        
    # 6. Metered Areas Translations & Grouping
    energy_col = "Metered Areas (Energy)"
    water_col = "Metered Areas (Water)"
    if energy_col in df.columns:
        df[energy_col] = df[energy_col].replace("Bâtiment complet", "Whole Property")
        
    partial_vals = ["Another configuration", "Common areas (all energy loads)", "Tenant areas (all energy loads)", "Tenant Plug Load/Electricity", "Tenant and/or common areas (partial energy loads)"]
    for col in [energy_col, water_col]:
        if col in df.columns:
            df[col] = df[col].replace(partial_vals, "Partial Property")
            
    # 7. Advanced City/Borough Logic (New York vs Outside)
    nyc_list = ["bronx", "beonx", "riverdale", "brooklyn", "bklyn", "booklyn", "bronklyn", "broo", "staten", "queens", "astoria", "astorea", "bayside", "bellerose", "briarwood", "arverne", "richmond", "ridgewood", "rockaway", "rockwy", "ozone", "springfield", "albans", "sunnyside", "maspeth", "middle village", "glendale", "hollis", "howard beach", "jackson", "jamaica", "kew gardens", "lic", "long island city", "little neck", "college point", "corona", "douglaston", "elmhurst", "edgemere", "floral park", "flushing", "fushing", "flushinig", "forest", "forrest", "fresh meadows", "glen oaks", "cambria", "rego park", "whitestone", "woodside", "manhattan", "manhatten", "tribeca", "chelsea", "new york", "ne york", "new", "ny", "nyc"]
    outside_list = ["buffalo", "denver", "long island", "new hyde park", "niagara", "westbury"]
    
    def fix_city(x):
        if pd.isna(x) or str(x).strip() == "": return np.nan
        xl = str(x).lower().strip()
        if any(kw in xl for kw in nyc_list):
            return "New York City"
        elif any(kw in xl for kw in outside_list):
            return str(x).title()
        return "Invalid/Address"
        
    if 'City' in df.columns:
        df['City2'] = df['City'].apply(fix_city)
        df = df[df['City2'] == "New York City"]
        df['City'] = df['City2']
        
    # 8. Alert Integrity & Outlier Filtering
    alerts_to_check = [
        "Alert - Data Center Issue (with Estimates, IT Configuration, or IT Meter)",
        "Alert - Energy Meter has less than 12 full calendar months of data",
        "Alert - Energy Meter has gaps",
        "Alert - Energy Meter has overlaps",
        "Alert - Energy Meter has single entry more than 65 days",
        "Alert - Water Meter has less than 12 full calendar months of data"
    ]
    for col in alerts_to_check:
        if col in df.columns:
            df = df[df[col] == "Ok"]
            
    if 'Base Penalty $/ft²' in df.columns:
        df = df[df['Base Penalty $/ft²'] < 1700]
        
    if 'Site Energy Use (kBtu)' in df.columns:
        df = df[df['Site Energy Use (kBtu)'] != 0]

    # 9. Clean Duplicates & Select Final Columns
    if 'Property Id' in df.columns:
        df = df.drop_duplicates(subset=['Property Id'])

    final_columns = [
        "Property Id", "Property Name", "Parent Property Id", "Parent Property Name", "City",
        "Primary Property Type - Portfolio Manager-Calculated", "Year Built", "Construction Status",
        "Occupancy", "Property GFA - Calculated (Buildings and Parking) (ft²)",
        "Property GFA - Calculated (Buildings) (ft²)", "Borough", "Metered Areas (Energy)",
        "Metered Areas (Water)", "ENERGY STAR Score", "National Median ENERGY STAR Score",
        "Target ENERGY STAR Score", "Site EUI (kBtu/ft²)", "Site Energy Use (kBtu)",
        "Source EUI (kBtu/ft²)", "Source Energy Use (kBtu)", "Green Power - Onsite and Offsite (kWh)",
        "eGRID Output Emissions Rate (kgCO2e/MBtu)", "Percent of Electricity that is Green Power",
        "Alert - Data Center Issue (with Estimates, IT Configuration, or IT Meter)",
        "Alert - Energy Meter has less than 12 full calendar months of data",
        "Alert - Energy Meter has gaps", "Alert - Energy Meter has overlaps",
        "Alert - Energy - No meters selected for metrics",
        "Alert - Energy Meter has single entry more than 65 days",
        "Alert - Water Meter has less than 12 full calendar months of data",
        "Alert - Property has no uses",
        "Avoided Emissions - Onsite and Offsite Green Power (Metric Tons CO2e)",
        "Total GHG Emissions (Metric Tons CO2e)", "Total GHG Emissions Intensity (kgCO2e/ft²)",
        "Net Emissions (Metric Tons CO2e)", "National Median Total GHG Emissions (Metric Tons CO2e)",
        "Building Age", "Base LL97 Penalty", "Base Penalty $/ft²", "Decade Built",
        "Fuel Oil #1 Use (kBtu)", "Fuel Oil #2 Use (kBtu)", "Fuel Oil #4 Use (kBtu)",
        "Fuel Oil #5 & 6 Use (kBtu)", "District Steam Use (kBtu)", "Diesel #2 Use (kBtu)",
        "District Hot Water Use (kBtu)", "District Chilled Water Use (kBtu)",
        "Natural Gas Use (kBtu)", "Electricity Use - Grid Purchase (kBtu)"
    ]
    
    existing_final_columns = [col for col in final_columns if col in df.columns]
    df = df[existing_final_columns]

    # 10. Save Output
    df.to_excel(output_path, index=False)
    print(f"Data processing complete! Output saved to {output_path}")
    return df

if __name__ == "__main__":
    pass
