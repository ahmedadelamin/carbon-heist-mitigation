import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import time
import os
import joblib

def train_strategic_model():
    print("="*60)
    print("   LL97 PREDICTIVE ENGINE V2.2 - STRATEGIC OPTIMIZER")
    print("="*60)
    
    # 1. Load Data
    file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/sample_nyc_energy.xlsx')
    print(f"[*] Step 1: Loading data from '{file_name}'...")
    
    if not os.path.exists(file_name):
        print(f"[!] ERROR: File '{file_name}' not found!")
        return

    try:
        # Loading .xlsx using openpyxl
        df = pd.read_excel(file_name)
        print(f"[+] Success: Loaded {len(df)} building records.")
    except Exception as e:
        print(f"[!] Error reading file: {e}")
        return

    # 2. Data Preprocessing
    print("[*] Step 2: Filtering outliers and handling missing values...")
    
    # Remove extreme outliers to prevent the model from getting 'confused'
    df = df[df['Site EUI (kBtu/ft²)'] < 2000]
    df = df[df['Property GFA - Calculated (Buildings and Parking) (ft²)'] > 0]
    
    # Fill missing Energy Star scores with the portfolio median
    df['ENERGY STAR Score'] = df['ENERGY STAR Score'].fillna(df['ENERGY STAR Score'].median())
    
    features = [
        'Year Built', 
        'Property GFA - Calculated (Buildings and Parking) (ft²)', 
        'ENERGY STAR Score',
        'Borough', 
        'Primary Property Type - Portfolio Manager-Calculated'
    ]
    target = 'Total GHG Emissions (Metric Tons CO2e)'
    
    df_ml = df.dropna(subset=features + [target]).copy()

    # 3. Categorical Encoding
    print("[*] Step 3: Encoding building categories...")
    le_borough = LabelEncoder()
    df_ml.loc[:, 'Borough_Enc'] = le_borough.fit_transform(df_ml['Borough'].astype(str))
    
    le_type = LabelEncoder()
    df_ml.loc[:, 'Type_Enc'] = le_type.fit_transform(df_ml['Primary Property Type - Portfolio Manager-Calculated'].astype(str))

    # Feature Matrix (X) and Target (y)
    X = df_ml[['Year Built', 'Property GFA - Calculated (Buildings and Parking) (ft²)', 'ENERGY STAR Score', 'Borough_Enc', 'Type_Enc']]
    y = df_ml[target]

    # 4. Training (Optimized Forest)
    print("[*] Step 4: Training Random Forest Regressor...")
    start_time = time.time()
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Increased estimators and adjusted depth for better pattern recognition
    model = RandomForestRegressor(n_estimators=150, max_depth=20, random_state=42)
    model.fit(X_train, y_train)
    
    end_time = time.time()
    print(f"[+] Training complete in {end_time - start_time:.2f} seconds.")

    # 5. Validation
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    print("\n" + "="*60)
    print("                MODEL PERFORMANCE REPORT")
    print("="*60)
    print(f"Predictive Accuracy (R²):          {r2:.4f} ({r2*100:.1f}%)")
    print(f"Mean Error (MAE):                  {mae:.2f} MT CO2e")
    print("-" * 60)

    # 6. Feature Importance
    importances = model.feature_importances_
    names = ['Year Built', 'GFA (Area)', 'Energy Star', 'Borough', 'Property Type']
    print("STRATEGIC INSIGHTS (Feature Weights):")
    for name, imp in zip(names, importances):
        print(f" - {name:15}: {imp:.2%}")
    print("="*60)

    # 7. Fixed Inference Test (Fixes the UserWarning)
    print("\n[*] Running AI Inference for 1930s Asset (150,000 sq ft)...")
    
    # We use a DataFrame here to match the training feature names and avoid warnings
    test_case = pd.DataFrame([[1930, 150000, 50, 3, 1]], columns=X.columns)
    test_prediction = model.predict(test_case)[0]
    
    penalty_psf = (test_prediction * 268) / 150000
    
    print(f"[+] Predicted Emissions: {test_prediction:.2f} MT CO2e")
    print(f"[+] Projected Penalty:   ${penalty_psf:.2f} /sq ft")
    print("-" * 60)

    # Save model and encoders
    model_dir = os.path.dirname(os.path.abspath(__file__))
    joblib.dump(model, os.path.join(model_dir, 'll97_model.joblib'))
    joblib.dump({'bor': le_borough, 'typ': le_type}, os.path.join(model_dir, 'll97_encoders.joblib'))
    print("[+] Model and encoders saved successfully!")

    return model

if __name__ == "__main__":
    trained_model = train_strategic_model()
    print("Model is ready for deployment in the Strategic Dashboard.")
    input("\nPress Enter to close...")