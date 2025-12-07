import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os

def train_model():
    # Load the data
    # Ensure we are in the right directory or use absolute path if needed
    # Assuming script is run from its location or paths are relative to it
    csv_path = 'fvg_analysis_XAUUSD_M15_4H.csv'
    if not os.path.exists(csv_path):
        # Try looking in the same directory as this script if running from elsewhere
        csv_path = os.path.join(os.path.dirname(__file__), 'fvg_analysis_XAUUSD_M15_4H.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)

    # --- Simplified Feature Engineering to match backtester ---

    # 1. Target Variable
    df['is_strong'] = (df['label'] == 'Strong').astype(int)

    # 2. Handle Categorical Features that the backtester can create
    categorical_features = ['FVG_Type', 'session', 'bias_H1']
    df = pd.get_dummies(df, columns=categorical_features, drop_first=True)

    # 3. Define features (X) and target (y) to match backtest_strategy.py
    # This list MUST match the one in the 'prepare_features' function of the backtester
    features_to_use = [
        'fvg_size',
        'volume_spike_at_fvg',
        'FVG_Type_Bullish',
        'session_London',
        'session_New York',
        'session_Other',
        'bias_H1_Bullish',
        'bias_H1_Neutral'
    ]

    # Ensure all expected columns exist in the dataframe, add if not
    for col in features_to_use:
        if col not in df.columns:
            df[col] = 0 # Add missing feature column, fill with 0

    X = df[features_to_use]
    y = df['is_strong']

    # Split data chronologically
    split_index = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
    y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]

    # --- Model Training ---
    lgbm = lgb.LGBMClassifier(objective='binary', is_unbalance=True, random_state=42)

    print("Training the harmonized model...")
    lgbm.fit(X_train, y_train)

    # --- Evaluation ---
    print("\n--- Model Evaluation on Unseen Data ---")
    y_pred = lgbm.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Not Strong', 'Strong']))

    # --- Feature Importance ---
    feature_importance = pd.DataFrame({'feature': X.columns, 'importance': lgbm.feature_importances_}).sort_values('importance', ascending=False)
    print("\n--- Feature Importance ---")
    print(feature_importance)

    # --- Save the final model and reports ---
    model_path = 'fvg_strong_classifier.joblib'
    # Save in the same dir as the script if possible, or current dir
    # If running from main_loop, we might want to save in TestAllModels/detect_FVG
    # But let's stick to relative path or absolute based on script location
    save_dir = os.path.dirname(__file__)
    model_full_path = os.path.join(save_dir, model_path)
    
    print(f"\nSaving the trained model to '{model_full_path}'...")
    joblib.dump(lgbm, model_full_path)
    
    report_path = os.path.join(save_dir, 'feature_importance.txt')
    with open(report_path, 'w') as f:
        f.write(feature_importance.to_string())

    print("\nProcess complete.")

if __name__ == "__main__":
    train_model()
