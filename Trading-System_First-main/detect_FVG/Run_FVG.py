"""
Run_FVG.py - Continuous FVG Monitoring and Trading Recommendation System

This script runs continuously with:
- Daily data updates and model retraining (2:00 AM)
- 15-minute FVG monitoring and alerts
- Logging system for all activities
- Notification system for trading opportunities

Usage:
    python Run_FVG.py
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import joblib
import os
import sys
from datetime import datetime, timedelta
import time
import warnings
import logging
from pathlib import Path

warnings.filterwarnings('ignore')

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import local modules
import fvg_analyzer
import train_fvg_classifier

# ==================== CONFIGURATION ====================
SYMBOL = 'XAUUSDm'
M15_CSV = 'XAUUSD_Candlestick_15_M_BID_31.10.2022-31.10.2025.csv'
H1_CSV = 'XAUUSD_Candlestick_1_Hour_BID_14.10.2010-31.10.2025.csv'
FVG_ANALYSIS_CSV = 'fvg_analysis_XAUUSD_M15_4H.csv'
MODEL_PATH = 'fvg_strong_classifier.joblib'

# Scheduling
DAILY_UPDATE_HOUR = 2  # 2:00 AM for daily updates
CHECK_INTERVAL_MINUTES = 15  # Check every 15 minutes
STRONG_THRESHOLD = 60  # Score threshold for "strong" FVG

# Notification settings
ENABLE_SOUND_ALERT = True  # Play sound on strong opportunity
ENABLE_LOG_FILE = True  # Save logs to file


class FVGTradingSystem:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.m15_csv_path = os.path.join(self.script_dir, M15_CSV)
        self.h1_csv_path = os.path.join(self.script_dir, H1_CSV)
        self.fvg_csv_path = os.path.join(self.script_dir, FVG_ANALYSIS_CSV)
        self.model_path = os.path.join(self.script_dir, MODEL_PATH)
        self.log_path = os.path.join(self.script_dir, 'fvg_monitor.log')
        
        self.mt5_initialized = False
        self.last_daily_update = None
        self.last_fvg_time = None  # Track last FVG to avoid duplicate alerts
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging system"""
        # Create logger
        self.logger = logging.getLogger('FVGMonitor')
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler (if enabled)
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
                
                # Display account info
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
    
    def fetch_latest_m15_candle(self):
        """Fetch only the latest M15 candle (lightweight check)"""
        if not self.mt5_initialized:
            if not self.initialize_mt5():
                return None
        
        # Fetch last 2 candles to ensure we get the complete one
        rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M15, 0, 2)
        
        if rates is None or len(rates) == 0:
            self.logger.warning("⚠️ No M15 data fetched")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        return df.iloc[-1]  # Return latest candle
    
    def full_data_update(self):
        """Full data update and model retraining (daily)"""
        self.logger.info("\n" + "="*60)
        self.logger.info("🔄 DAILY DATA UPDATE & MODEL RETRAINING")
        self.logger.info("="*60)
        
        try:
            # Fetch and update data
            self._fetch_and_update_data()
            
            # Run FVG analysis
            self._run_fvg_analysis()
            
            # Train classifier
            self._train_classifier()
            
            self.last_daily_update = datetime.now()
            self.logger.info(f"✅ Daily update completed at {self.last_daily_update.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            self.logger.error(f"❌ Daily update failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _fetch_and_update_data(self):
        """Fetch latest data from MT5 and update CSV files"""
        if not self.mt5_initialized:
            if not self.initialize_mt5():
                raise Exception("Failed to initialize MT5")
        
        # Verify symbol
        symbol_info = mt5.symbol_info(SYMBOL)
        if symbol_info is None:
            raise ValueError(f"Symbol {SYMBOL} not available")
        
        if not symbol_info.visible:
            mt5.symbol_select(SYMBOL, True)
        
        # Fetch M15 data
        self.logger.info("📥 Fetching M15 data...")
        self._update_csv_with_new_data(
            timeframe=mt5.TIMEFRAME_M15,
            csv_path=self.m15_csv_path,
            days=7,
            timeframe_name="M15"
        )
        
        # Fetch H1 data
        self.logger.info("📥 Fetching H1 data...")
        self._update_csv_with_new_data(
            timeframe=mt5.TIMEFRAME_H1,
            csv_path=self.h1_csv_path,
            days=7,
            timeframe_name="H1"
        )
    
    def _update_csv_with_new_data(self, timeframe, csv_path, days, timeframe_name):
        """Helper function to fetch data and update CSV"""
        utc_to = datetime.now()
        utc_from = utc_to - timedelta(days=days)
        
        rates = mt5.copy_rates_range(SYMBOL, timeframe, utc_from, utc_to)
        
        if rates is None or len(rates) == 0:
            self.logger.warning(f"⚠️ No new data for {timeframe_name}")
            return
        
        # Convert to DataFrame
        new_df = pd.DataFrame(rates)
        new_df['time'] = pd.to_datetime(new_df['time'], unit='s')
        new_df = new_df.rename(columns={
            'time': 'Gmt time',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'tick_volume': 'Volume'
        })
        new_df = new_df[['Gmt time', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        # Load and merge with existing data
        if os.path.exists(csv_path):
            existing_df = pd.read_csv(csv_path, parse_dates=['Gmt time'], dayfirst=True)
            last_timestamp = existing_df['Gmt time'].max()
            new_df = new_df[new_df['Gmt time'] > last_timestamp]
            
            if len(new_df) > 0:
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['Gmt time'], keep='last')
                combined_df = combined_df.sort_values('Gmt time')
                combined_df.to_csv(csv_path, index=False, date_format='%d.%m.%Y %H:%M:%S.000')
                self.logger.info(f"✅ Added {len(new_df)} new {timeframe_name} candles")
            else:
                self.logger.info(f"ℹ️ No new {timeframe_name} data to add")
        else:
            new_df.to_csv(csv_path, index=False, date_format='%d.%m.%Y %H:%M:%S.000')
            self.logger.info(f"✅ Created {timeframe_name} CSV with {len(new_df)} candles")
    
    def _run_fvg_analysis(self):
        """Run FVG analyzer"""
        self.logger.info("🔍 Running FVG Analysis...")
        original_dir = os.getcwd()
        os.chdir(self.script_dir)
        
        try:
            fvg_analyzer.main()
            self.logger.info("✅ FVG analysis completed")
        except Exception as e:
            self.logger.error(f"❌ FVG analysis failed: {e}")
            raise
        finally:
            os.chdir(original_dir)
    
    def _train_classifier(self):
        """Train/update the FVG classifier model"""
        self.logger.info("🤖 Training FVG Classifier...")
        original_dir = os.getcwd()
        os.chdir(self.script_dir)
        
        try:
            train_fvg_classifier.train_model()
            self.logger.info("✅ Model training completed")
        except Exception as e:
            self.logger.error(f"❌ Model training failed: {e}")
            raise
        finally:
            os.chdir(original_dir)
    
    def check_for_opportunity(self):
        """Lightweight 15-minute check for trading opportunities"""
        try:
            # Load FVG analysis data
            if not os.path.exists(self.fvg_csv_path):
                self.logger.warning("⚠️ FVG analysis file not found")
                return None
            
            fvg_data = pd.read_csv(self.fvg_csv_path)
            fvg_data['time_created'] = pd.to_datetime(fvg_data['time_created'])
            
            if len(fvg_data) == 0:
                return None
            
            # Get the most recent FVG
            latest_fvg = fvg_data.iloc[-1]
            
            # Skip if we already alerted for this FVG
            if self.last_fvg_time == latest_fvg['time_created']:
                return None
            
            # Load model
            if not os.path.exists(self.model_path):
                self.logger.warning("⚠️ Model not found")
                return None
            
            model = joblib.load(self.model_path)
            
            # Prepare features and predict
            features_df = self._prepare_features(latest_fvg)
            model_features = model.booster_.feature_name()
            features_aligned = features_df.reindex(columns=model_features, fill_value=0)
            
            probability = model.predict_proba(features_aligned)[0, 1]
            score = int(probability * 100)
            is_strong = score >= STRONG_THRESHOLD
            
            # Calculate direction
            direction = self._calculate_direction(latest_fvg)
            
            # Create recommendation
            recommendation = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'fvg_time': latest_fvg['time_created'],
                'fvg_type': latest_fvg['FVG_Type'],
                'fvg_size': latest_fvg['fvg_size'],
                'fvg_bottom': latest_fvg['fvg_bottom'],
                'fvg_top': latest_fvg['fvg_top'],
                'score': score,
                'is_strong': is_strong,
                'direction': direction['action'],
                'h1_trend': direction['h1_trend'],
                'm15_trend': direction['m15_trend']
            }
            
            # Only alert if strong and actionable
            if is_strong and direction['action'] in ['BUY', 'SELL']:
                self.last_fvg_time = latest_fvg['time_created']
                return recommendation
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Check failed: {e}")
            return None
    
    def _prepare_features(self, fvg_row):
        """Prepare features for model prediction"""
        df = pd.DataFrame([fvg_row])
        categorical_features = ['FVG_Type', 'session', 'bias_H1']
        df = pd.get_dummies(df, columns=categorical_features, drop_first=True)
        
        expected_features = [
            'fvg_size', 'volume_spike_at_fvg', 'FVG_Type_Bullish',
            'session_London', 'session_New York', 'session_Other',
            'bias_H1_Bullish', 'bias_H1_Neutral'
        ]
        
        for feat in expected_features:
            if feat not in df.columns:
                df[feat] = 0
        
        return df
    
    def _calculate_direction(self, latest_fvg):
        """Calculate trading direction based on trends"""
        m15_df = pd.read_csv(self.m15_csv_path, parse_dates=['Gmt time'], dayfirst=True)
        h1_df = pd.read_csv(self.h1_csv_path, parse_dates=['Gmt time'], dayfirst=True)
        
        # Calculate trends
        m15_df['sma50'] = m15_df['Close'].rolling(window=50).mean()
        latest_m15 = m15_df.iloc[-1]
        m15_trend = 'Up' if latest_m15['Close'] > latest_m15['sma50'] else 'Down'
        
        h1_df['sma50'] = h1_df['Close'].rolling(window=50).mean()
        latest_h1 = h1_df.iloc[-1]
        h1_trend = 'Up' if latest_h1['Close'] > latest_h1['sma50'] else 'Down'
        
        # Determine action
        fvg_type = latest_fvg['FVG_Type']
        
        if fvg_type == 'Bullish' and m15_trend == 'Up' and h1_trend == 'Up':
            action = 'BUY'
        elif fvg_type == 'Bearish' and m15_trend == 'Down' and h1_trend == 'Down':
            action = 'SELL'
        else:
            action = 'WAIT'
        
        return {'action': action, 'm15_trend': m15_trend, 'h1_trend': h1_trend}
    
    def send_alert(self, recommendation):
        """Send alert for trading opportunity"""
        self.logger.info("\n" + "="*60)
        self.logger.info("🚨 TRADING OPPORTUNITY DETECTED!")
        self.logger.info("="*60)
        self.logger.info(f"⏰ Time: {recommendation['timestamp']}")
        self.logger.info(f"📍 FVG Created: {recommendation['fvg_time']}")
        self.logger.info(f"📊 Type: {recommendation['fvg_type']}")
        self.logger.info(f"📏 Size: {recommendation['fvg_size']:.2f} points")
        self.logger.info(f"📈 Range: {recommendation['fvg_bottom']:.2f} - {recommendation['fvg_top']:.2f}")
        self.logger.info(f"\n💪 STRONG AREA: YES ✅")
        self.logger.info(f"📊 Score: {recommendation['score']}%")
        self.logger.info(f"\n📈 M15 Trend: {recommendation['m15_trend']}")
        self.logger.info(f"📈 H1 Trend: {recommendation['h1_trend']}")
        self.logger.info(f"\n🎯 DIRECTION: {recommendation['direction']}")
        self.logger.info("="*60)
        
        # Sound alert (Windows beep)
        if ENABLE_SOUND_ALERT:
            try:
                import winsound
                winsound.Beep(1000, 500)  # 1000 Hz for 500ms
            except:
                pass
    
    def should_run_daily_update(self):
        """Check if it's time for daily update"""
        now = datetime.now()
        
        # First run or after midnight
        if self.last_daily_update is None:
            return True
        
        # Check if it's the scheduled hour and we haven't updated today
        if now.hour == DAILY_UPDATE_HOUR and now.date() > self.last_daily_update.date():
            return True
        
        return False
    
    def run_continuous(self):
        """Main continuous monitoring loop"""
        self.logger.info("\n" + "="*60)
        self.logger.info("🚀 FVG CONTINUOUS MONITORING STARTED")
        self.logger.info("="*60)
        self.logger.info(f"⏰ Daily Update Time: {DAILY_UPDATE_HOUR}:00 AM")
        self.logger.info(f"🔄 Check Interval: Every {CHECK_INTERVAL_MINUTES} minutes")
        self.logger.info(f"📊 Strong Threshold: {STRONG_THRESHOLD}%")
        self.logger.info("="*60)
        
        # Initialize MT5
        if not self.initialize_mt5():
            self.logger.error("❌ Cannot start without MT5 connection")
            return
        
        # Run initial daily update
        self.full_data_update()
        
        try:
            while True:
                # Check if daily update is needed
                if self.should_run_daily_update():
                    self.full_data_update()
                
                # Check for opportunities
                self.logger.info(f"\n⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for opportunities...")
                recommendation = self.check_for_opportunity()
                
                if recommendation:
                    self.send_alert(recommendation)
                else:
                    self.logger.info("ℹ️ No strong opportunities at this time")
                
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
    system = FVGTradingSystem()
    system.run_continuous()


if __name__ == "__main__":
    main()
