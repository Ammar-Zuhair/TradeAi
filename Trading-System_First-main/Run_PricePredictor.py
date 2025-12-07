"""
Run_PricePredictor.py - Continuous Price Prediction Monitoring System

This script runs continuously with:
- Daily data updates and model retraining (2:00 AM)
- 15-minute price predictions
- Logging system for all activities
- Alert system for significant price movements

Usage:
    python Run_PricePredictor.py
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import joblib
import lightgbm as lgb
from sklearn.preprocessing import StandardScaler
import os
import sys
from datetime import datetime, timedelta
import time
import warnings
import logging

warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ==================== CONFIGURATION ====================
SYMBOL = 'XAUUSD'
CSV_FILE = 'XAUUSD-15M.csv'
MODEL_DIR = 'saved_model_single_train_Full'
CHARTS_DIR = 'horizon_charts_single_train_Full'

# Scheduling
DAILY_UPDATE_HOUR = 2  # 2:00 AM for daily updates
CHECK_INTERVAL_MINUTES = 15  # Predict every 15 minutes

# Alert settings
ENABLE_SOUND_ALERT = True
ENABLE_LOG_FILE = True
PRICE_CHANGE_THRESHOLD = 0.5  # Alert if predicted change > 0.5%


class PricePredictionSystem:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.csv_path = os.path.join(self.script_dir, CSV_FILE)
        self.model_dir = os.path.join(self.script_dir, MODEL_DIR)
        self.charts_dir = os.path.join(self.script_dir, CHARTS_DIR)
        self.log_path = os.path.join(self.script_dir, 'price_predictor.log')
        
        self.mt5_initialized = False
        self.last_daily_update = None
        self.last_prediction = None
        
        # Ensure directories exist
        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs(self.charts_dir, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging system"""
        self.logger = logging.getLogger('PricePredictor')
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler
        if ENABLE_LOG_FILE:
            file_handler = logging.FileHandler(self.log_path, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
    
    def initialize_mt5(self):
        """Initialize MetaTrader 5 connection with retry logic"""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                if not mt5.initialize():
                    raise Exception(f"MT5 initialization failed: {mt5.last_error()}")
                
                self.logger.info("✅ MT5 initialized successfully")
                
                account_info = mt5.account_info()
                if account_info:
                    self.logger.info(f"📊 Account: {account_info.login} | Balance: ${account_info.balance:.2f}")
                
                self.mt5_initialized = True
                return True
                
            except Exception as e:
                self.logger.warning(f"⚠️ MT5 init attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    self.logger.error("❌ Failed to initialize MT5 after all retries")
                    return False
    
    def fetch_and_update_m15_data(self):
        """Fetch latest M15 data and update CSV"""
        if not self.mt5_initialized:
            if not self.initialize_mt5():
                raise Exception("Failed to initialize MT5")
        
        # Verify symbol
        symbol_info = mt5.symbol_info(SYMBOL)
        if symbol_info is None:
            raise ValueError(f"Symbol {SYMBOL} not available")
        
        if not symbol_info.visible:
            mt5.symbol_select(SYMBOL, True)
        
        # Fetch M15 data (last 7 days)
        utc_to = datetime.now()
        utc_from = utc_to - timedelta(days=7)
        
        rates = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M15, utc_from, utc_to)
        
        if rates is None or len(rates) == 0:
            self.logger.warning("⚠️ No M15 data fetched")
            return
        
        # Convert to DataFrame
        new_df = pd.DataFrame(rates)
        new_df['time'] = pd.to_datetime(new_df['time'], unit='s')
        new_df = new_df.rename(columns={
            'time': 'date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'tick_volume': 'Volume'
        })
        new_df = new_df[['date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        # Format date to match expected format
        new_df['date'] = new_df['date'].dt.strftime('%d.%m.%Y %H:%M:%S.000')
        
        # Load and merge with existing data
        if os.path.exists(self.csv_path):
            existing_df = pd.read_csv(self.csv_path)
            
            # Parse existing dates
            existing_df['date'] = pd.to_datetime(existing_df['date'], format='%d.%m.%Y %H:%M:%S.%f')
            new_df['date'] = pd.to_datetime(new_df['date'], format='%d.%m.%Y %H:%M:%S.%f')
            
            last_timestamp = existing_df['date'].max()
            new_df = new_df[new_df['date'] > last_timestamp]
            
            if len(new_df) > 0:
                # Format back to string
                existing_df['date'] = existing_df['date'].dt.strftime('%d.%m.%Y %H:%M:%S.000')
                new_df['date'] = new_df['date'].dt.strftime('%d.%m.%Y %H:%M:%S.000')
                
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_csv(self.csv_path, index=False)
                self.logger.info(f"✅ Added {len(new_df)} new M15 candles")
            else:
                self.logger.info("ℹ️ No new M15 data to add")
        else:
            new_df.to_csv(self.csv_path, index=False)
            self.logger.info(f"✅ Created CSV with {len(new_df)} candles")
    
    def create_features(self):
        """Create and save feature list"""
        features = [
            'open', 'high', 'low', 'close', 'volume',
            'ret_1', 'ret_3', 'ret_5', 'ret_10', 'ret_20',
            'sma_s', 'sma_m', 'sma_l',
            'ema_s', 'ema_m', 'ema_l',
            'sma_spread_sm', 'sma_spread_ml',
            'ema_spread_sm', 'ema_spread_ml',
            'atr14', 'vol_sd', 'bb_z', 'rsi',
            'sin_dow', 'cos_dow', 'sin_dom', 'cos_dom'
        ]
        
        features_path = os.path.join(self.model_dir, 'XAUUSD_features.joblib')
        joblib.dump(features, features_path)
        self.logger.info(f"✅ Features file created")
    
    def train_model(self):
        """Train the price prediction model"""
        self.logger.info("🤖 Training price prediction model...")
        
        # Load data
        df = pd.read_csv(self.csv_path)
        df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y %H:%M:%S.%f', utc=True)
        df = df.rename(columns={'Open':'open','High':'high','Low':'low','Close':'close','Volume':'volume'})
        df = df.set_index('date').sort_index()
        df = df[['open','high','low','close','volume']].dropna()
        df = df[(df['high'] >= df['low']) & (df['open'] > 0) & (df['close'] > 0)]
        
        # Feature engineering
        df = self._add_features(df)
        
        # Prepare training data
        features = [col for col in df.columns if col not in ['target_r1']]
        X = df[features]
        y = df['target_r1']
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train LightGBM model
        lgb_params = dict(
            objective='regression',
            metric='l2',
            learning_rate=0.03,
            num_leaves=63,
            feature_fraction=0.9,
            bagging_fraction=0.9,
            bagging_freq=1,
            min_data_in_leaf=25,
            verbose=-1,
            seed=42
        )
        
        train_ds = lgb.Dataset(X_scaled, label=y, feature_name=list(X.columns))
        model = lgb.train(lgb_params, train_ds, num_boost_round=1200)
        
        # Save model and scaler
        model_path = os.path.join(self.model_dir, 'XAUUSD_lgbm_model.txt')
        scaler_path = os.path.join(self.model_dir, 'XAUUSD_scaler.joblib')
        
        model.save_model(model_path)
        joblib.dump(scaler, scaler_path)
        
        self.logger.info("✅ Model training completed")
    
    def _add_features(self, df):
        """Add technical features to dataframe"""
        x = df.copy()
        c = x['close']
        
        # Returns
        x['ret_1'] = np.log(c).diff(1)
        for k in [3,5,10,20]:
            x[f'ret_{k}'] = np.log(c).diff(k)
        
        # Moving averages
        x['sma_s'] = c.rolling(5).mean()
        x['sma_m'] = c.rolling(20).mean()
        x['sma_l'] = c.rolling(60).mean()
        x['ema_s'] = c.ewm(span=5, adjust=False).mean()
        x['ema_m'] = c.ewm(span=20, adjust=False).mean()
        x['ema_l'] = c.ewm(span=60, adjust=False).mean()
        x['sma_spread_sm'] = (x['sma_s'] - x['sma_m']) / c
        x['sma_spread_ml'] = (x['sma_m'] - x['sma_l']) / c
        x['ema_spread_sm'] = (x['ema_s'] - x['ema_m']) / c
        x['ema_spread_ml'] = (x['ema_m'] - x['ema_l']) / c
        
        # Volatility
        tr = np.maximum(x['high']-x['low'],
                        np.maximum((x['high']-c.shift(1)).abs(), (x['low']-c.shift(1)).abs()))
        x['atr14'] = tr.rolling(14).mean() / c
        x['vol_sd'] = x['ret_1'].rolling(30).std()
        
        # Bollinger & RSI
        ma = c.rolling(20).mean()
        sd = c.rolling(20).std()
        x['bb_z'] = (c - ma) / (sd + 1e-12)
        
        delta = c.diff()
        up = delta.clip(lower=0).rolling(14).mean()
        down = (-delta.clip(upper=0)).rolling(14).mean()
        rs = up / (down + 1e-12)
        x['rsi'] = 100 - (100 / (1 + rs))
        
        # Time encoding
        dow = x.index.dayofweek
        x['sin_dow'] = np.sin(2*np.pi*dow/7)
        x['cos_dow'] = np.cos(2*np.pi*dow/7)
        dom = x.index.day
        x['sin_dom'] = np.sin(2*np.pi*dom/31)
        x['cos_dom'] = np.cos(2*np.pi*dom/31)
        
        # Target
        x['target_r1'] = np.log(c.shift(-1)) - np.log(c)
        
        x = x.dropna()
        return x
    
    def predict_next_price(self):
        """Predict next close price"""
        try:
            # Load model and scaler
            model_path = os.path.join(self.model_dir, 'XAUUSD_lgbm_model.txt')
            scaler_path = os.path.join(self.model_dir, 'XAUUSD_scaler.joblib')
            features_path = os.path.join(self.model_dir, 'XAUUSD_features.joblib')
            
            if not all(os.path.exists(p) for p in [model_path, scaler_path, features_path]):
                self.logger.warning("⚠️ Model files not found")
                return None
            
            model = lgb.Booster(model_file=model_path)
            scaler = joblib.load(scaler_path)
            feature_names = joblib.load(features_path)
            
            # Load and prepare data
            df = pd.read_csv(self.csv_path)
            df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y %H:%M:%S.%f')
            df = df.rename(columns={'Open':'open','High':'high','Low':'low','Close':'close','Volume':'volume'})
            df = df.set_index('date').sort_index()
            df = df[['open','high','low','close','volume']].dropna()
            
            # Add features
            df = self._add_features(df)
            
            # Get latest data point
            latest = df.iloc[-1]
            current_price = latest['close']
            
            # Prepare features
            X = df[feature_names].iloc[-1:].copy()
            X_scaled = scaler.transform(X)
            
            # Predict
            predicted_log_return = model.predict(X_scaled)[0]
            predicted_price = current_price * np.exp(predicted_log_return)
            
            # Calculate change
            price_change = predicted_price - current_price
            price_change_pct = (price_change / current_price) * 100
            
            prediction = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'current_price': current_price,
                'predicted_price': predicted_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'direction': 'UP' if price_change > 0 else 'DOWN'
            }
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"❌ Prediction failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def send_prediction_alert(self, prediction):
        """Send alert for price prediction"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📈 PRICE PREDICTION")
        self.logger.info("="*60)
        self.logger.info(f"⏰ Time: {prediction['timestamp']}")
        self.logger.info(f"💰 Current Price: {prediction['current_price']:.2f}")
        self.logger.info(f"🎯 Predicted Price (Next 15min): {prediction['predicted_price']:.2f}")
        self.logger.info(f"📊 Expected Change: {prediction['price_change']:+.2f} ({prediction['price_change_pct']:+.2f}%)")
        self.logger.info(f"🔄 Direction: {prediction['direction']}")
        self.logger.info("="*60)
        
        # Sound alert for significant changes
        if abs(prediction['price_change_pct']) >= PRICE_CHANGE_THRESHOLD and ENABLE_SOUND_ALERT:
            try:
                import winsound
                winsound.Beep(1500, 300)
            except:
                pass
    
    def full_daily_update(self):
        """Full daily update: data + features + training"""
        self.logger.info("\n" + "="*60)
        self.logger.info("🔄 DAILY UPDATE & MODEL RETRAINING")
        self.logger.info("="*60)
        
        try:
            # Fetch data
            self.logger.info("📥 Fetching M15 data...")
            self.fetch_and_update_m15_data()
            
            # Create features
            self.logger.info("🔧 Creating features...")
            self.create_features()
            
            # Train model
            self.train_model()
            
            self.last_daily_update = datetime.now()
            self.logger.info(f"✅ Daily update completed at {self.last_daily_update.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            self.logger.error(f"❌ Daily update failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def should_run_daily_update(self):
        """Check if it's time for daily update"""
        now = datetime.now()
        
        if self.last_daily_update is None:
            return True
        
        if now.hour == DAILY_UPDATE_HOUR and now.date() > self.last_daily_update.date():
            return True
        
        return False
    
    def run_continuous(self):
        """Main continuous monitoring loop"""
        self.logger.info("\n" + "="*60)
        self.logger.info("🚀 PRICE PREDICTION MONITORING STARTED")
        self.logger.info("="*60)
        self.logger.info(f"⏰ Daily Update Time: {DAILY_UPDATE_HOUR}:00 AM")
        self.logger.info(f"🔄 Prediction Interval: Every {CHECK_INTERVAL_MINUTES} minutes")
        self.logger.info("="*60)
        
        # Initialize MT5
        if not self.initialize_mt5():
            self.logger.error("❌ Cannot start without MT5 connection")
            return
        
        # Run initial daily update
        self.full_daily_update()
        
        try:
            while True:
                # Check if daily update is needed
                if self.should_run_daily_update():
                    self.full_daily_update()
                
                # Make prediction
                self.logger.info(f"\n⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Predicting next price...")
                prediction = self.predict_next_price()
                
                if prediction:
                    self.send_prediction_alert(prediction)
                    self.last_prediction = prediction
                else:
                    self.logger.info("ℹ️ Prediction not available")
                
                # Wait for next check
                self.logger.info(f"💤 Sleeping for {CHECK_INTERVAL_MINUTES} minutes...")
                time.sleep(CHECK_INTERVAL_MINUTES * 60)
                
        except KeyboardInterrupt:
            self.logger.info("\n⚠️ Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"\n❌ Critical error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            self.shutdown_mt5()
    
    def shutdown_mt5(self):
        """Shutdown MT5 connection"""
        if self.mt5_initialized:
            mt5.shutdown()
            self.logger.info("✅ MT5 connection closed")
            self.mt5_initialized = False


def main():
    """Main entry point"""
    system = PricePredictionSystem()
    system.run_continuous()


if __name__ == "__main__":
    main()
