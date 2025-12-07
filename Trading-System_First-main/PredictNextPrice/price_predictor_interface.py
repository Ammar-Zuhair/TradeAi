import pandas as pd
import numpy as np
import joblib
import lightgbm as lgb
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'saved_model_single_train_Full')

class PricePredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.load_model()

    def load_model(self):
        try:
            model_path = os.path.join(MODEL_DIR, 'XAUUSD_lgbm_model.txt')
            scaler_path = os.path.join(MODEL_DIR, 'XAUUSD_scaler.joblib')
            features_path = os.path.join(MODEL_DIR, 'XAUUSD_features.joblib') # Assuming this exists based on prediction_comparison.py

            if os.path.exists(model_path):
                self.model = lgb.Booster(model_file=model_path)
            else:
                print(f"⚠️ Price Prediction Model not found at {model_path}")

            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
            else:
                print(f"⚠️ Scaler not found at {scaler_path}")
            
            if os.path.exists(features_path):
                self.feature_names = joblib.load(features_path)
            else:
                 # Fallback if features file doesn't exist, try to infer or hardcode if necessary
                 # Based on train_model_single_batch.py, features are columns in df_feat except target
                 print(f"⚠️ Features file not found at {features_path}. Will attempt to use all columns from processed data.")
                 self.feature_names = None

        except Exception as e:
            print(f"❌ Error loading Price Prediction model: {e}")

    def preprocess_data(self, df):
        """
        Prepares the dataframe for prediction.
        Expects a DataFrame with columns: 'open', 'high', 'low', 'close', 'volume' (lowercase).
        """
        df = df.copy()
        # Ensure columns are lowercase
        df.columns = df.columns.str.lower()
        
        # Feature Engineering (Must match training logic)
        c = df['close']
        
        # Returns
        df['ret_1'] = np.log(c).diff(1)
        for k in [3, 5, 10, 20]:
            df[f'ret_{k}'] = np.log(c).diff(k)

        # Moving Averages
        win_s, win_m, win_l = 5, 20, 60
        df['sma_s'] = c.rolling(win_s).mean()
        df['sma_m'] = c.rolling(win_m).mean()
        df['sma_l'] = c.rolling(win_l).mean()
        
        df['ema_s'] = c.ewm(span=win_s, adjust=False).mean()
        df['ema_m'] = c.ewm(span=win_m, adjust=False).mean()
        df['ema_l'] = c.ewm(span=win_l, adjust=False).mean()
        
        df['sma_spread_sm'] = (df['sma_s'] - df['sma_m']) / c
        df['sma_spread_ml'] = (df['sma_m'] - df['sma_l']) / c
        df['ema_spread_sm'] = (df['ema_s'] - df['ema_m']) / c
        df['ema_spread_ml'] = (df['ema_m'] - df['ema_l']) / c

        # Volatility (ATR)
        tr = np.maximum(df['high'] - df['low'],
                        np.maximum((df['high'] - c.shift(1)).abs(), (df['low'] - c.shift(1)).abs()))
        df['atr14'] = tr.rolling(14).mean() / c
        df['vol_sd'] = df['ret_1'].rolling(30).std()

        # Bollinger Bands
        ma = c.rolling(win_m).mean()
        sd = c.rolling(win_m).std()
        df['bb_z'] = (c - ma) / (sd + 1e-12)

        # RSI
        delta = c.diff()
        up = delta.clip(lower=0).rolling(14).mean()
        down = (-delta.clip(upper=0)).rolling(14).mean()
        rs = up / (down + 1e-12)
        df['rsi'] = 100 - (100 / (1 + rs))

        # Date Features
        if not isinstance(df.index, pd.DatetimeIndex):
             # Try to parse if 'date' or 'Gmt time' column exists
             if 'date' in df.columns:
                 df['date'] = pd.to_datetime(df['date'])
                 df.set_index('date', inplace=True)
             elif 'gmt time' in df.columns:
                 df['gmt time'] = pd.to_datetime(df['gmt time'])
                 df.set_index('gmt time', inplace=True)
        
        if isinstance(df.index, pd.DatetimeIndex):
            dow = df.index.dayofweek
            df['sin_dow'] = np.sin(2 * np.pi * dow / 7)
            df['cos_dow'] = np.cos(2 * np.pi * dow / 7)
            dom = df.index.day
            df['sin_dom'] = np.sin(2 * np.pi * dom / 31)
            df['cos_dom'] = np.cos(2 * np.pi * dom / 31)
        else:
            # Fallback if no datetime index (should not happen in production flow)
            df['sin_dow'] = 0
            df['cos_dow'] = 0
            df['sin_dom'] = 0
            df['cos_dom'] = 0

        return df

    def predict_next(self, df):
        """
        Predicts the next close price based on the latest data in df.
        Returns: (predicted_price, predicted_direction)
        predicted_direction: 'Buy' if predicted > current, 'Sell' if predicted < current
        """
        if self.model is None or self.scaler is None:
            print("⚠️ Model or Scaler not loaded. Cannot predict.")
            return None, None

        try:
            # Process data
            df_processed = self.preprocess_data(df)
            
            # Get the last row (latest candle)
            # Note: We need enough history for rolling windows (max 60). 
            # Assuming df passed has enough history.
            
            if len(df_processed) < 60:
                print("⚠️ Not enough data for prediction features (need > 60 candles).")
                return None, None

            last_row = df_processed.iloc[[-1]].copy()
            
            # Select features
            if self.feature_names:
                # Ensure all features exist
                missing_cols = [col for col in self.feature_names if col not in last_row.columns]
                if missing_cols:
                    print(f"⚠️ Missing features for prediction: {missing_cols}")
                    # Try to fill with 0 or handle
                    for col in missing_cols:
                        last_row[col] = 0
                
                X = last_row[self.feature_names]
            else:
                # Fallback: use all columns except target if defined, or just use what we have that matches training
                # This is risky. Better to rely on feature_names.
                # Assuming train_model_single_batch.py features:
                features = [col for col in last_row.columns if col not in ['target_r1', 'open', 'high', 'low', 'close', 'volume', 'date', 'gmt time']]
                X = last_row[features]

            # Scale
            X_scaled = self.scaler.transform(X)

            # Predict (Log Return)
            pred_log_return = self.model.predict(X_scaled)[0]
            
            # Convert to Price
            current_close = last_row['close'].iloc[0]
            predicted_close = current_close * np.exp(pred_log_return)
            
            direction = 'Buy' if predicted_close > current_close else 'Sell'
            
            return predicted_close, direction

        except Exception as e:
            print(f"❌ Error during price prediction: {e}")
            return None, None

if __name__ == "__main__":
    # Test
    predictor = PricePredictor()
    # Load sample data
    try:
        df = pd.read_csv(os.path.join(BASE_DIR, '../XAUUSD-15M.csv')) # Adjust path as needed
        # Mock date parsing if needed
        if 'Gmt time' in df.columns:
             df['date'] = pd.to_datetime(df['Gmt time'], dayfirst=True)
             df.set_index('date', inplace=True)
             
        price, direction = predictor.predict_next(df.tail(200))
        print(f"Predicted Price: {price}, Direction: {direction}")
    except Exception as e:
        print(f"Test failed: {e}")
