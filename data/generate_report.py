import pandas as pd
import numpy as np
from fpdf import FPDF
import os

# Create a PDF class
class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'LL97 Data Cleaning & Reduction Report', border=False, ln=True, align='C')
        self.ln(10)

    def chapter_title(self, step_num, title, rows_before, rows_after):
        self.set_font('helvetica', 'B', 12)
        self.set_fill_color(200, 220, 255)
        diff = rows_before - rows_after
        self.cell(0, 8, f'Step {step_num}: {title}', border=True, ln=True, fill=True)
        self.set_font('helvetica', '', 11)
        self.cell(0, 8, f'Rows Before: {rows_before:,} | Rows After: {rows_after:,} | Dropped: {diff:,}', border=False, ln=True)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('helvetica', '', 10)
        self.multi_cell(0, 6, body)
        self.ln(6)

def generate_pdf():
    raw_path = r'C:\Users\ahmed\OneDrive\Desktop\carbon-heist-mitigation\data\Raw_Data_Energy_and_Water_Data_Disclosure_for_Local_Law_84_2022_(Data_for_Calendar_Year_2021)_20260221.xlsx'
    df = pd.read_excel(raw_path, sheet_name=0)
    
    pdf = PDF()
    pdf.add_page()
    
    # 0. Initial
    initial_rows = len(df)
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 10, f'Initial Raw Data Rows: {initial_rows:,}', ln=True)
    pdf.ln(5)

    step = 1
    
    # Replace Not Available
    rows_before = len(df)
    df = df.replace("Not Available", np.nan)
    pdf.chapter_title(step, 'Standardizing Null Values', rows_before, len(df))
    pdf.chapter_body("Replaced the text 'Not Available' with standard system NULL (NaN) values to allow numeric filtering. This step doesn't drop rows, but prepares the data.")
    step += 1

    # Construction Status
    rows_before = len(df)
    if 'Construction Status' in df.columns:
        df = df[df['Construction Status'] != "Test"]
    pdf.chapter_title(step, 'Filtering Test Properties', rows_before, len(df))
    pdf.chapter_body("Removed properties marked as 'Test' in the Construction Status column, keeping only real assets.")
    step += 1

    # GFA > 50000
    rows_before = len(df)
    gfa_col = "Property GFA - Calculated (Buildings and Parking) (ft²)"
    if gfa_col in df.columns:
        df[gfa_col] = pd.to_numeric(df[gfa_col], errors='coerce')
        df = df[df[gfa_col] >= 50000]
    pdf.chapter_title(step, 'LL97 Size Threshold Filter', rows_before, len(df))
    pdf.chapter_body("Filtered properties to only include buildings with a Gross Floor Area (GFA) >= 50,000 sq ft, matching the Local Law 97 regulatory baseline.")
    step += 1

    # City filter
    rows_before = len(df)
    nyc_list = ["bronx", "beonx", "riverdale", "brooklyn", "bklyn", "booklyn", "bronklyn", "broo", "staten", "queens", "astoria", "astorea", "bayside", "bellerose", "briarwood", "arverne", "richmond", "ridgewood", "rockaway", "rockwy", "ozone", "springfield", "albans", "sunnyside", "maspeth", "middle village", "glendale", "hollis", "howard beach", "jackson", "jamaica", "kew gardens", "lic", "long island city", "little neck", "college point", "corona", "douglaston", "elmhurst", "edgemere", "floral park", "flushing", "fushing", "flushinig", "forest", "forrest", "fresh meadows", "glen oaks", "cambria", "rego park", "whitestone", "woodside", "manhattan", "manhatten", "tribeca", "chelsea", "new york", "ne york", "new", "ny", "nyc"]
    outside_list = ["buffalo", "denver", "long island", "new hyde park", "niagara", "westbury"]
    def fix_city(x):
        if pd.isna(x) or str(x).strip() == "": return np.nan
        xl = str(x).lower().strip()
        if any(kw in xl for kw in nyc_list): return "New York City"
        elif any(kw in xl for kw in outside_list): return str(x).title()
        return "Invalid/Address"
    if 'City' in df.columns:
        city_replacements = {"Ny": "New York", "New York City": "New York", "Quuens": "Queens", "The Bronx": "Bronx", "Queens,": "Queens", "Quens": "Queens", "Queen": "Queens", "New York,": "New York", "New Yok": "New York", "New Yrk": "New York", "New Yorkc": "New York", "beonx": "Bronx", "bronx": "Bronx"}
        df['City'] = df['City'].replace(city_replacements)
        df['City'] = df['City'].str.title().str.strip()
        df['City2'] = df['City'].apply(fix_city)
        df = df[df['City2'] == "New York City"]
    pdf.chapter_title(step, 'New York City Boundaries Filter', rows_before, len(df))
    pdf.chapter_body("Processed typo-ridden city names and filtered the dataset to strictly contain addresses within New York City boroughs (dropping out-of-state/invalid locations).")
    step += 1

    # Alerts
    rows_before = len(df)
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
            df[col] = df[col].replace("OK", "Ok")
            df = df[df[col] == "Ok"]
    pdf.chapter_title(step, 'Data Integrity & Alerts Filter', rows_before, len(df))
    pdf.chapter_body("Dropped records containing critical missing or overlapping meter data (e.g., energy gaps, less than 12 months of data) to ensure emissions baseline accuracy.")
    step += 1

    # Penalty Outliers
    rows_before = len(df)
    ghg_col = "Total GHG Emissions (Metric Tons CO2e)"
    if ghg_col in df.columns:
        df[ghg_col] = pd.to_numeric(df[ghg_col], errors='coerce')
        df['Base Penalty $/ft²'] = (df[ghg_col] * 268) / df[gfa_col]
        df = df[df['Base Penalty $/ft²'] < 1700]
    pdf.chapter_title(step, 'Penalty Outliers Filter', rows_before, len(df))
    pdf.chapter_body("Calculated projected carbon penalties and removed extreme statistical outliers (Penalty > $1700/sqft) likely resulting from data entry errors.")
    step += 1

    # Site Energy Use = 0
    rows_before = len(df)
    if 'Site Energy Use (kBtu)' in df.columns:
        df['Site Energy Use (kBtu)'] = pd.to_numeric(df['Site Energy Use (kBtu)'], errors='coerce')
        df = df[df['Site Energy Use (kBtu)'] != 0]
    pdf.chapter_title(step, 'Zero Energy Use Filter', rows_before, len(df))
    pdf.chapter_body("Dropped records where reported site energy use was exactly zero (which is physically impossible for operating buildings).")
    step += 1

    # Duplicates
    rows_before = len(df)
    if 'Property Id' in df.columns:
        df = df.drop_duplicates(subset=['Property Id'])
    pdf.chapter_title(step, 'Remove Duplicate Property IDs', rows_before, len(df))
    pdf.chapter_body("Removed duplicate rows based on Property ID, retaining only unique buildings in the final dataset.")
    step += 1
    
    # Final Result
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_fill_color(150, 255, 150)
    pdf.cell(0, 10, f'Final Clean Data Rows: {len(df):,}', border=True, ln=True, fill=True, align='C')
    pdf.ln(5)
    
    pdf.set_font('helvetica', 'I', 10)
    pdf.cell(0, 10, f'Total Rows Dropped: {initial_rows - len(df):,} ({(initial_rows - len(df))/initial_rows*100:.1f}%)', ln=True, align='C')

    output_path = r'C:\Users\ahmed\OneDrive\Desktop\carbon-heist-mitigation\Data_Cleaning_Report.pdf'
    pdf.output(output_path)
    print("Report generated:", output_path)

if __name__ == '__main__':
    generate_pdf()
