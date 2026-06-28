import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import os

# --- LL97 CURRENT LIMITS (2024-2029 Phase) ---
# Simplified to focus on immediate regulatory reality based on current law
CURRENT_LIMITS = {
    'Office': 0.00846,
    'Multifamily Housing': 0.00675,
    'Hotel': 0.00987,
    'Retail Store': 0.01181,
    'Default': 0.00750
}

def get_data_driven_insights(year, score, emissions, gfa, prop_type, avg_emissions_data):
    """
    Diagnostic engine focusing on current peer comparison (Data-Driven).
    """
    diagnosis = []
    recommendations = []
    
    # 1. Comparison with Peer Data (The "Power of Data")
    avg_peer_emissions = avg_emissions_data * (gfa / 100000) # Scaling mean to building size
    efficiency_gap = ((emissions - avg_peer_emissions) / avg_peer_emissions) * 100
    
    if efficiency_gap > 0:
        diagnosis.append(f"Performance Gap: This building emits {efficiency_gap:.1f}% MORE than its peers in the dataset.")
        recommendations.append("- Operational Audit: Review current HVAC schedules and lighting controls.")
    else:
        diagnosis.append(f"High Performer: This building emits {abs(efficiency_gap):.1f}% LESS than the dataset average.")
        recommendations.append("- Maintenance: Continue preventive maintenance to maintain this competitive edge.")

    # 2. Specific Asset Diagnosis
    if year < 1945:
        diagnosis.append(f"Vintage Profile: Built in {int(year)}. High risk of envelope energy leakage.")
        recommendations.append("- Insulation Check: Inspect roof and window seals for thermal loss.")
    
    if score < 50:
        diagnosis.append(f"Efficiency Risk: Low Energy Star Score ({score}) indicates potential system obsolescence.")
        recommendations.append("- Smart Tech: Implement LED retrofits and sub-metering for better visibility.")

    return diagnosis, recommendations, efficiency_gap

def train_current_model(file_name):
    """
    Trains the model based strictly on current patterns found in the CSV/Excel.
    """
    print("[*] Training Phase: Analyzing current patterns in 11,000+ records...")
    df = pd.read_excel(file_name)
    
    # Cleaning based on current data distribution
    df = df[df['Site EUI (kBtu/ft²)'] < 1500]
    df = df[df['Property GFA - Calculated (Buildings and Parking) (ft²)'] > 25000]
    df['ENERGY STAR Score'] = df['ENERGY STAR Score'].fillna(df['ENERGY STAR Score'].median())
    
    target = 'Total GHG Emissions (Metric Tons CO2e)'
    features = ['Year Built', 'Property GFA - Calculated (Buildings and Parking) (ft²)', 'ENERGY STAR Score', 'Borough', 'Primary Property Type - Portfolio Manager-Calculated']
    
    df_ml = df.dropna(subset=features + [target])
    
    # Calculating global average emissions for benchmarking
    global_avg_emissions = df_ml[target].mean()
    
    le_bor = LabelEncoder()
    df_ml['Borough_Enc'] = le_bor.fit_transform(df_ml['Borough'].astype(str))
    le_typ = LabelEncoder()
    df_ml['Type_Enc'] = le_typ.fit_transform(df_ml['Primary Property Type - Portfolio Manager-Calculated'].astype(str))
    
    X = df_ml[['Year Built', 'Property GFA - Calculated (Buildings and Parking) (ft²)', 'ENERGY STAR Score', 'Borough_Enc', 'Type_Enc']]
    y = df_ml[target]
    
    model = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42)
    model.fit(X, y)
    
    joblib.dump(model, 'll97_model.joblib')
    joblib.dump({'bor': le_bor, 'typ': le_typ, 'avg': global_avg_emissions}, 'll97_encoders.joblib')
    
    return model, {'bor': le_bor, 'typ': le_typ, 'avg': global_avg_emissions}, X.columns

def start_playground():
    print("\n" + "═"*80)
    print("   LL97 DATA-DRIVEN INSIGHTS ENGINE - CURRENT STATUS ONLY")
    print("═"*80)
    
    file_name = '1234.xlsx - Clean.csv.xlsx'
    if not os.path.exists(file_name):
        print(f"Error: Database '{file_name}' not found.")
        return

    model, encoders, feature_cols = train_current_model(file_name)
    
    while True:
        print("\n" + ">>> CURRENT ASSET ANALYSIS" + " -" * 25)
        try:
            year_in = input("Year Built [or 'exit']: ")
            if year_in.lower() == 'exit': break
            
            year = float(year_in)
            gfa = float(input("GFA (sq ft): "))
            score = float(input("Energy Star Score (1-100): "))
            
            bor_name = input(f"Borough ({', '.join(encoders['bor'].classes_[:3])}...): ").strip()
            bor_code = encoders['bor'].transform([bor_name])[0] if bor_name in encoders['bor'].classes_ else encoders['bor'].transform(['Manhattan'])[0]

            type_name = input("Property Type (e.g., Office): ").strip()
            type_code = encoders['typ'].transform([type_name])[0] if type_name in encoders['typ'].classes_ else encoders['typ'].transform(['Office'])[0]

            # 1. AI EMISSION PREDICTION
            test_df = pd.DataFrame([[year, gfa, score, bor_code, type_code]], columns=feature_cols)
            predicted_emissions = model.predict(test_df)[0]
            
            # 2. CARBON LIABILITY CALCULATION (Non-Zero Metric)
            # We calculate the cost per sqft for 100% of emissions to show total exposure
            liability_psf = (predicted_emissions * 268) / gfa
            
            # 3. DATA-DRIVEN INSIGHTS
            diag, recs, gap = get_data_driven_insights(year, score, predicted_emissions, gfa, type_name, encoders['avg'])

            # 4. REPORT
            print("\n" + "╔" + "═"*70 + "╗")
            print(f"║ STRATEGIC AUDIT: {type_name.upper()} IN {bor_name.upper()} ".ljust(71) + "║")
            print("╠" + "═"*70 + "╣")
            print(f"║ [PREDICTED EMISSIONS]  {predicted_emissions:.1f} Metric Tons CO2e/yr".ljust(71) + "║")
            print(f"║ [CARBON LIABILITY]     ${liability_psf:.2f} /sqft (Total Exposure)".ljust(71) + "║")
            print(f"║ [PEER COMPARISON]      {'+' if gap > 0 else ''}{gap:.1f}% vs. Portfolio Avg".ljust(71) + "║")
            print("╠" + "═"*70 + "╣")
            print("║ [DATA DIAGNOSIS]".ljust(71) + "║")
            for d in diag: print(f"║  • {d}".ljust(71) + "║")
            print("║".ljust(71) + "║")
            print("║ [CURRENT RECOMMENDATIONS]".ljust(71) + "║")
            for r in recs: print(f"║  {r}".ljust(71) + "║")
            print("╚" + "═"*70 + "╝")

        except Exception as e:
            print(f"(!) Input Error: {e}")

if __name__ == "__main__":
    start_playground()