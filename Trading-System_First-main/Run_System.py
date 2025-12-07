"""
Run_System.py - Integrated Trading System
=========================================

This is the MAIN orchestration system that coordinates all trading components:
1. Daily news fetch (high-impact events)
2. 15-minute news check (skip trading if news within ±30 min)
3. FVG analysis (detect strong areas)
4. Price prediction (next 15-min close)
5. Volume & Momentum models (voting system)
6. Final trading recommendation

Usage:
    python Run_System.py
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import joblib
import os
import sys
from datetime import datetime, timedelta
import time
import math
import warnings
import logging
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler, StandardScaler

# Load environment variables
try:
    from env_loader import Config
    Config.validate()  # Validate credentials on startup
except ImportError:
    print("Warning: env_loader.py not found. Using default configuration.")
    class Config:
        MT5_LOGIN = ''
        MT5_PASSWORD = ''
        MT5_SERVER = ''
        SYMBOL = 'XAUUSD'
        ENABLE_AUTO_TRADING = False
        RISK_PERCENTAGE = 1.0
        ENABLE_SOUND_ALERT = True
        ENABLE_LOG_FILE = True
        CHECK_INTERVAL_MINUTES = 15
        NEWS_WINDOW_MINUTES = 30

warnings.filterwarnings('ignore')

# Add subdirectories to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'detect_FVG'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'PredictNextPrice'))

# ==================== CONFIGURATION ====================
# Load from environment variables (Config class)
SYMBOL = Config.SYMBOL if hasattr(Config, 'SYMBOL') else 'XAUUSD'
NEWS_CSV = 'recommendations.csv'
MODELS_DIR = 'models'
SCALERS_DIR = 'scalers'

# Scheduling
DAILY_UPDATE_HOUR = 2  # 2:00 AM
CHECK_INTERVAL_MINUTES = Config.CHECK_INTERVAL_MINUTES if hasattr(Config, 'CHECK_INTERVAL_MINUTES') else 15
NEWS_WINDOW_MINUTES = Config.NEWS_WINDOW_MINUTES if hasattr(Config, 'NEWS_WINDOW_MINUTES') else 30

# Alert settings
ENABLE_SOUND_ALERT = Config.ENABLE_SOUND_ALERT if hasattr(Config, 'ENABLE_SOUND_ALERT') else True
ENABLE_LOG_FILE = Config.ENABLE_LOG_FILE if hasattr(Config, 'ENABLE_LOG_FILE') else True

# Trade execution settings
ENABLE_AUTO_TRADING = Config.ENABLE_AUTO_TRADING if hasattr(Config, 'ENABLE_AUTO_TRADING') else False
RISK_PERCENTAGE = Config.RISK_PERCENTAGE if hasattr(Config, 'RISK_PERCENTAGE') else 1.0
MIN_LOT_SIZE = 0.01  # Minimum lot size
MAX_LOT_SIZE = 10.0  # Maximum lot size for safety
FIXED_SL_PIPS = 30  # Fixed SL for non-FVG trades (in pips)
FIXED_TP_PIPS = 90  # Fixed TP for non-FVG trades (in pips)


class IntegratedTradingSystem:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.news_csv_path = os.path.join(self.script_dir, NEWS_CSV)
        self.models_dir = os.path.join(self.script_dir, MODELS_DIR)
        self.scalers_dir = os.path.join(self.script_dir, SCALERS_DIR)
        self.log_path = os.path.join(self.script_dir, 'trading_system.log')
        
        self.mt5_initialized = False
        self.last_daily_update = None
        self.last_news_fetch = None
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging system"""
        self.logger = logging.getLogger('TradingSystem')
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
        """Initialize MetaTrader 5 connection with credentials from .env"""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                # Try to get credentials from Config
                if hasattr(Config, 'get_mt5_credentials'):
                    try:
                        credentials = Config.get_mt5_credentials()
                        self.logger.info("🔐 Using MT5 credentials from .env file")
                        
                        # Initialize with login
                        if not mt5.initialize(
                            login=credentials['login'],
                            password=credentials['password'],
                            server=credentials['server']
                        ):
                            raise Exception(f"MT5 initialization failed: {mt5.last_error()}")
                    except ValueError as ve:
                        self.logger.warning(f"⚠️ .env validation failed: {ve}")
                        self.logger.info("Attempting initialization without credentials...")
                        if not mt5.initialize():
                            raise Exception(f"MT5 initialization failed: {mt5.last_error()}")
                else:
                    # Fallback: initialize without credentials
                    self.logger.info("ℹ️ No .env credentials found, using default initialization")
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
    
    def fetch_daily_news(self):
        """Fetch high-impact news using getNews.py"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📰 FETCHING DAILY NEWS")
        self.logger.info("="*60)
        
        try:
            # Run getNews.py
            import subprocess
            result = subprocess.run(
                [sys.executable, os.path.join(self.script_dir, 'getNews.py')],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.logger.info("✅ News fetched successfully")
                self.last_news_fetch = datetime.now()
            else:
                self.logger.error(f"❌ News fetch failed: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"❌ News fetch error: {e}")
    
    def check_news_window(self):
        """Check if there's high-impact news within ±30 minutes"""
        if not os.path.exists(self.news_csv_path):
            return False  # No news file, safe to trade
        
        try:
            news_df = pd.read_csv(self.news_csv_path, encoding='utf-8')
            
            if len(news_df) == 0:
                return False
            
            now = datetime.now()
            
            for _, row in news_df.iterrows():
                # Parse news time
                news_date = row['تاريخ الحدث']  # Date
                news_time = row['الوقت']  # Time
                
                # Combine date and time
                try:
                    news_datetime = datetime.strptime(f"{news_date} {news_time}", "%Y-%m-%d %I:%M%p")
                except:
                    try:
                        news_datetime = datetime.strptime(f"{news_date} {news_time}", "%Y-%m-%d %H:%M")
                    except:
                        continue
                
                # Check if within window
                time_diff = abs((news_datetime - now).total_seconds() / 60)
                
                if time_diff <= NEWS_WINDOW_MINUTES:
                    self.logger.warning(f"⚠️ HIGH-IMPACT NEWS DETECTED!")
                    self.logger.warning(f"   Event: {row['الحدث']}")
                    self.logger.warning(f"   Time: {news_datetime}")
                    self.logger.warning(f"   Minutes away: {time_diff:.1f}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ News check error: {e}")
            return False  # If error, assume safe to trade
    
    def run_fvg_analysis(self):
        """Run FVG analysis and get recommendation"""
        self.logger.info("\n📊 Running FVG Analysis...")
        
        try:
            # Import FVG system
            from detect_FVG.Run_FVG import FVGTradingSystem
            
            fvg_system = FVGTradingSystem()
            
            # Initialize MT5 if not already
            if not fvg_system.mt5_initialized:
                fvg_system.initialize_mt5()
            
            # Check for opportunity
            recommendation = fvg_system.check_for_opportunity()
            
            if recommendation and recommendation['is_strong']:
                self.logger.info(f"✅ FVG: STRONG AREA ({recommendation['score']}%)")
                self.logger.info(f"   Direction: {recommendation['direction']}")
                return recommendation
            else:
                self.logger.info("ℹ️ FVG: No strong area detected")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ FVG analysis failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def predict_next_price(self):
        """Predict next 15-min close price"""
        self.logger.info("\n💰 Predicting Next Price...")
        
        try:
            # Import price predictor
            from PredictNextPrice.Run_PricePredictor import PricePredictionSystem
            
            price_system = PricePredictionSystem()
            
            # Get prediction
            prediction = price_system.predict_next_price()
            
            if prediction:
                self.logger.info(f"✅ Price Prediction:")
                self.logger.info(f"   Current: {prediction['current_price']:.2f}")
                self.logger.info(f"   Predicted: {prediction['predicted_price']:.2f}")
                self.logger.info(f"   Change: {prediction['price_change']:+.2f} ({prediction['price_change_pct']:+.2f}%)")
                self.logger.info(f"   Direction: {prediction['direction']}")
                return prediction
            else:
                self.logger.info("ℹ️ Price prediction not available")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Price prediction failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def get_volume_momentum_votes(self):
        """Get predictions from volume and momentum models"""
        self.logger.info("\n🗳️ Getting Volume & Momentum Votes...")
        
        try:
            # Fetch market data
            if not self.mt5_initialized:
                self.initialize_mt5()
            
            # Get data
            utc_to = datetime.now()
            utc_from = utc_to - timedelta(days=7)
            rates = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M15, utc_from, utc_to)
            
            if rates is None or len(rates) == 0:
                self.logger.warning("⚠️ No market data available")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            df.rename(columns={
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'tick_volume': 'volume'
            }, inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            # Calculate indicators
            volume_data = self._calculate_volume_indicators(df)
            momentum_data = self._calculate_momentum_indicators(df)
            
            # Load models and scalers
            volume_model = keras.models.load_model(os.path.join(self.models_dir, 'Conv1D_Deep_volume.keras'))
            momentum_model = keras.models.load_model(os.path.join(self.models_dir, 'Conv1D_Deep_momentum.keras'))
            
            # Normalize and predict
            volume_pred = self._predict_with_model(volume_model, volume_data, 'volume')
            momentum_pred = self._predict_with_model(momentum_model, momentum_data, 'momentum')
            
            self.logger.info(f"✅ Volume Model: {volume_pred['action']}")
            self.logger.info(f"✅ Momentum Model: {momentum_pred['action']}")
            
            return {
                'volume': volume_pred,
                'momentum': momentum_pred
            }
            
        except Exception as e:
            self.logger.error(f"❌ Volume/Momentum prediction failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _calculate_volume_indicators(self, df):
        """Calculate volume indicators"""
        data = df.copy()
        
        # VWAP
        data['vwap'] = (data['volume'] * (data['high'] + data['low'] + data['close']) / 3).cumsum() / data['volume'].cumsum()
        
        # Volume ROC
        data['volume_roc'] = data['volume'].pct_change(periods=14) * 100
        
        # CMF
        mf_multiplier = ((data['close'] - data['low']) - (data['high'] - data['close'])) / (data['high'] - data['low'])
        mf_volume = mf_multiplier * data['volume']
        data['cmf'] = mf_volume.rolling(window=20).sum() / data['volume'].rolling(window=20).sum()
        
        # A/D Line Change
        data['ad_line'] = (mf_multiplier * data['volume']).cumsum()
        data['ad_line_change'] = data['ad_line'].diff()
        
        return data[['close', 'vwap', 'volume_roc', 'cmf', 'ad_line_change', 'volume']].iloc[-1:].copy()
    
    def _calculate_momentum_indicators(self, df):
        """Calculate momentum indicators"""
        data = df.copy()
        
        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # Stochastic
        low_14 = data['low'].rolling(window=14).min()
        high_14 = data['high'].rolling(window=14).max()
        data['stoch_k'] = 100 * ((data['close'] - low_14) / (high_14 - low_14))
        data['stoch_d'] = data['stoch_k'].rolling(window=3).mean()
        
        # CCI
        tp = (data['high'] + data['low'] + data['close']) / 3
        sma_tp = tp.rolling(window=20).mean()
        mad = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
        data['cci'] = (tp - sma_tp) / (0.015 * mad)
        
        # MFI
        mf = tp * data['volume']
        mf_pos = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
        mf_neg = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
        data['mfi'] = 100 - (100 / (1 + mf_pos / mf_neg))
        
        # Williams %R
        data['williams_r'] = -100 * ((high_14 - data['close']) / (high_14 - low_14))
        
        return data[['volume', 'rsi', 'stoch_k', 'stoch_d', 'cci', 'mfi', 'williams_r']].iloc[-1:].copy()
    
    def _predict_with_model(self, model, data, model_name):
        """Predict with a model"""
        # Load scaler
        scaler_path = os.path.join(self.scalers_dir, f'{model_name}_standard_scaler.pkl')
        
        if os.path.exists(scaler_path):
            scaler = joblib.load(scaler_path)
            data_scaled = scaler.transform(data)
        else:
            data_scaled = data.values
        
        # Predict
        prediction = model.predict(data_scaled, verbose=0)
        pred_class = np.argmax(prediction, axis=1)[0]
        confidence = np.max(prediction)
        
        # Convert to action
        actions = ['SELL', 'HOLD', 'BUY']
        action = actions[pred_class] if pred_class < len(actions) else 'HOLD'
        
        return {
            'action': action,
            'confidence': confidence,
            'prediction': pred_class
        }
    
    def get_full_voting_recommendation(self):
        """Get recommendation from all 7 models using getDataAndVoting.py logic"""
        self.logger.info("\n🗳️ Running Full Voting System (7 Models)...")
        
        try:
            from getDataAndVoting import MarketPredictionSystem
            
            voting_system = MarketPredictionSystem(
                symbol=SYMBOL,
                models_dir=self.models_dir,
                scalers_dir=self.scalers_dir
            )
            
            # Initialize MT5 if needed
            if not voting_system.mt5_initialized:
                voting_system.initialize_mt5()
            
            # Fetch market data
            voting_system.fetch_market_data(timeframe=mt5.TIMEFRAME_M15, days=7)
            
            # Get final recommendation
            result = voting_system.get_final_recommendation()
            
            if result:
                self.logger.info(f"✅ Full Voting Result: {result['recommendation'].upper()}")
                self.logger.info(f"   Confidence: {result['confidence']:.2%}")
                return result
            else:
                self.logger.info("ℹ️ Full voting not available")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Full voting failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def make_final_decision(self, fvg, price_pred, vm_votes):
        """Make final trading decision based on all inputs"""
        self.logger.info("\n" + "="*60)
        self.logger.info("🎯 FINAL DECISION MAKING")
        self.logger.info("="*60)
        
        # Collect all signals
        signals = []
        
        # FVG signal
        if fvg:
            signals.append(fvg['direction'])
            self.logger.info(f"FVG Signal: {fvg['direction']}")
        
        # Price prediction signal
        if price_pred:
            signals.append(price_pred['direction'])
            self.logger.info(f"Price Signal: {price_pred['direction']}")
        
        # Volume & Momentum signals
        if vm_votes:
            if vm_votes['volume']['action'] != 'HOLD':
                signals.append(vm_votes['volume']['action'])
            if vm_votes['momentum']['action'] != 'HOLD':
                signals.append(vm_votes['momentum']['action'])
            self.logger.info(f"Volume Signal: {vm_votes['volume']['action']}")
            self.logger.info(f"Momentum Signal: {vm_votes['momentum']['action']}")
        
        # Count votes
        if not signals:
            self.logger.info("❌ No signals available")
            return None
        
        buy_votes = signals.count('BUY') + signals.count('UP')
        sell_votes = signals.count('SELL') + signals.count('DOWN')
        
        self.logger.info(f"\n📊 Vote Count:")
        self.logger.info(f"   BUY votes: {buy_votes}")
        self.logger.info(f"   SELL votes: {sell_votes}")
        
        # Decision logic: Need at least 3 matching signals
        if buy_votes >= 3:
            final_action = 'BUY'
        elif sell_votes >= 3:
            final_action = 'SELL'
        else:
            final_action = 'WAIT'
        
        self.logger.info(f"\n🎯 FINAL DECISION: {final_action}")
        
        return {
            'action': final_action,
            'buy_votes': buy_votes,
            'sell_votes': sell_votes,
            'total_signals': len(signals),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    
    def calculate_lot_size(self, sl_distance_points):
        """Calculate lot size based on risk management (2% risk per trade)"""
        try:
            # Get account balance
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.warning("⚠️ Cannot get account info - using minimum lot size")
                return MIN_LOT_SIZE
            
            balance = account_info.balance
            
            # Get symbol info for contract size
            symbol_info = mt5.symbol_info(SYMBOL)
            if symbol_info is None:
                self.logger.warning("⚠️ Cannot get symbol info - using minimum lot size")
                return MIN_LOT_SIZE
            
            # Calculate risk amount in account currency
            risk_amount = balance * (RISK_PERCENTAGE / 100)
            
            # Get contract size (for XAUUSD usually 100)
            contract_size = symbol_info.trade_contract_size
            
            # Calculate pip value for 1 lot
            # For XAUUSD: 1 pip = 0.01, so pip value = contract_size * 0.01
            pip_value_per_lot = contract_size * 0.01
            
            # Calculate lot size
            # Risk Amount = Lot Size × Pip Value × SL in Pips
            # Lot Size = Risk Amount / (Pip Value × SL in Pips)
            sl_distance_pips = sl_distance_points / 10  # Convert points to pips
            
            if sl_distance_pips <= 0:
                self.logger.warning("⚠️ Invalid SL distance - using minimum lot size")
                return MIN_LOT_SIZE
            
            calculated_lot_size = risk_amount / (pip_value_per_lot * sl_distance_pips)
            
            # Apply minimum lot size constraint
            if calculated_lot_size < MIN_LOT_SIZE:
                self.logger.info(f"📊 Calculated lot size ({calculated_lot_size:.3f}) < minimum, using {MIN_LOT_SIZE}")
                calculated_lot_size = MIN_LOT_SIZE
            
            # Apply maximum lot size constraint for safety
            if calculated_lot_size > MAX_LOT_SIZE:
                self.logger.warning(f"⚠️ Calculated lot size ({calculated_lot_size:.3f}) > maximum, using {MAX_LOT_SIZE}")
                calculated_lot_size = MAX_LOT_SIZE
            
            # Floor to 2 decimal places (e.g. 0.025 -> 0.02)
            calculated_lot_size = math.floor(calculated_lot_size * 100) / 100
            
            self.logger.info(f"\n💰 Risk Management Calculation:")
            self.logger.info(f"   Account Balance: ${balance:.2f}")
            self.logger.info(f"   Risk Percentage: {RISK_PERCENTAGE}%")
            self.logger.info(f"   Risk Amount: ${risk_amount:.2f}")
            self.logger.info(f"   SL Distance: {sl_distance_pips:.1f} pips")
            self.logger.info(f"   Calculated Lot Size: {calculated_lot_size}")
            
            return calculated_lot_size
            
        except Exception as e:
            self.logger.error(f"❌ Lot size calculation failed: {e}")
            self.logger.warning(f"⚠️ Using minimum lot size: {MIN_LOT_SIZE}")
            return MIN_LOT_SIZE
    
    def execute_trade(self, decision, fvg_data=None):
        """Execute trade on MT5 with SL/TP based on FVG (Limit Orders) or fixed values"""
        if not ENABLE_AUTO_TRADING:
            self.logger.info("ℹ️ Auto-trading disabled - Recommendation only")
            return False
        
        if not self.mt5_initialized:
            self.logger.error("❌ Cannot execute trade - MT5 not initialized")
            return False
        
        action = decision['action']
        if action not in ['BUY', 'SELL']:
            return False
        
        try:
            # Get symbol info
            symbol_info = mt5.symbol_info(SYMBOL)
            if symbol_info is None:
                self.logger.error(f"❌ Symbol {SYMBOL} not found")
                return False
            
            # Get current price
            tick = mt5.symbol_info_tick(SYMBOL)
            if tick is None:
                self.logger.error("❌ Failed to get current price")
                return False
            
            current_ask = tick.ask
            current_bid = tick.bid
            point = symbol_info.point
            
            # Default values
            order_type = mt5.ORDER_TYPE_BUY if action == 'BUY' else mt5.ORDER_TYPE_SELL
            price = current_ask if action == 'BUY' else current_bid
            type_filling = mt5.ORDER_FILLING_IOC
            
            # Logic Split: FVG vs Non-FVG
            if fvg_data and 'fvg_size' in fvg_data:
                # --- FVG STRATEGY (Limit Orders + 1:5 RR) ---
                fvg_bottom = fvg_data.get('fvg_bottom')
                fvg_top = fvg_data.get('fvg_top')
                fvg_size = fvg_data.get('fvg_size')
                
                # Constants for FVG strategy
                SPREAD_POINTS = 0.5 * point * 10  # Assuming point is 0.01 for XAUUSD, 0.5 points = 0.5
                # Note: The user code used 0.5 as absolute value. For XAUUSD 1 point = 1.0 usually in price? 
                # Let's stick to the user's formula logic: 0.5 "points" usually means 0.5 USD in Gold.
                # If symbol.point is 0.01, then 0.5 USD is 50 points. 
                # User said "Spread: 0.5 points". In XAUUSD context, 0.5 price difference is standard.
                SPREAD_PRICE = 0.5 
                
                self.logger.info(f"\n📏 FVG Advanced Strategy (1:5 RR):")
                
                if action == 'BUY':
                    # Entry: FVG Bottom + Spread
                    entry_price = fvg_bottom + SPREAD_PRICE
                    
                    # SL: FVG Bottom - 1.0 + (0.1 * FVG Size)
                    # Note: User formula: fvg_bottom - STOP_LOSS_POINTS + row['fvg_size'] * 0.1
                    # STOP_LOSS_POINTS was 1.0
                    sl = fvg_bottom - 1.0 + (fvg_size * 0.1)
                    
                    # Risk
                    risk_per_trade = entry_price - sl
                    
                    # TP: 1:5 Ratio
                    tp = entry_price + (risk_per_trade * 5.0)
                    
                    # Determine Order Type (Limit vs Market)
                    # If current Ask is significantly higher than entry, use Limit
                    # If current Ask is below or near entry, use Market (IOC)
                    if current_ask > entry_price:
                        order_type = mt5.ORDER_TYPE_BUY_LIMIT
                        price = entry_price
                        type_filling = mt5.ORDER_FILLING_RETURN
                        self.logger.info("   Type: BUY LIMIT (Price Retracement Needed)")
                    else:
                        order_type = mt5.ORDER_TYPE_BUY
                        price = current_ask # Execute at market
                        self.logger.info("   Type: BUY MARKET (Price within/below zone)")
                        
                else:  # SELL
                    # Entry: FVG Top - Spread
                    entry_price = fvg_top - SPREAD_PRICE
                    
                    # SL: FVG Top + 1.0
                    # Note: User formula: fvg_top + STOP_LOSS_POINTS
                    sl = fvg_top + 1.0
                    
                    # Risk
                    risk_per_trade = sl - entry_price
                    
                    # TP: 1:5 Ratio
                    tp = entry_price - (risk_per_trade * 5.0)
                    
                    # Determine Order Type
                    # If current Bid is significantly lower than entry, use Limit
                    if current_bid < entry_price:
                        order_type = mt5.ORDER_TYPE_SELL_LIMIT
                        price = entry_price
                        type_filling = mt5.ORDER_FILLING_RETURN
                        self.logger.info("   Type: SELL LIMIT (Price Retracement Needed)")
                    else:
                        order_type = mt5.ORDER_TYPE_SELL
                        price = current_bid # Execute at market
                        self.logger.info("   Type: SELL MARKET (Price within/above zone)")

                self.logger.info(f"   Entry Target: {entry_price:.2f}")
                self.logger.info(f"   Stop Loss: {sl:.2f}")
                self.logger.info(f"   Take Profit: {tp:.2f}")
                self.logger.info(f"   Risk: {risk_per_trade:.2f} | Reward: {risk_per_trade * 5:.2f}")
                
            else:
                # --- NON-FVG STRATEGY (Fixed Pips) ---
                self.logger.info(f"\n📏 Fixed SL/TP Calculation (Non-FVG):")
                self.logger.info(f"   SL: {FIXED_SL_PIPS} pips")
                self.logger.info(f"   TP: {FIXED_TP_PIPS} pips")
                
                if action == 'BUY':
                    sl = current_ask - (FIXED_SL_PIPS * 10 * point)
                    tp = current_ask + (FIXED_TP_PIPS * 10 * point)
                else:  # SELL
                    sl = current_bid + (FIXED_SL_PIPS * 10 * point)
                    tp = current_bid - (FIXED_TP_PIPS * 10 * point)
            
            # Calculate lot size based on risk management
            # For Limit orders, use the limit price. For Market, use current.
            sl_distance_points = abs(sl - price)
            # Convert price difference to points (assuming XAUUSD 2 digits = 100 points per $)
            # Actually calculate_lot_size expects "points" as in MT5 points (0.01)
            # So distance 1.0 USD = 100 points.
            # Let's pass the raw price difference and let calculate_lot_size handle it?
            # Looking at calculate_lot_size: "sl_distance_pips = sl_distance_points / 10"
            # It expects MT5 points. 
            # XAUUSD point = 0.01. 
            # If SL distance is $1.0, that is 100 points.
            sl_distance_mt5_points = sl_distance_points / point
            
            lot_size = self.calculate_lot_size(sl_distance_mt5_points)
            
            request = {
                "action": mt5.TRADE_ACTION_PENDING if order_type in [mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_SELL_LIMIT] else mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234000,
                "comment": f"FVG_Sys_1:5" if fvg_data else "Voting_Sys",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": type_filling,
            }
            
            # Log order details
            self.logger.info(f"\n📋 Order Details:")
            self.logger.info(f"   Symbol: {SYMBOL}")
            self.logger.info(f"   Action: {action}")
            self.logger.info(f"   Type: {'LIMIT' if 'LIMIT' in str(order_type) else 'MARKET'}")
            self.logger.info(f"   Lot Size: {lot_size}")
            self.logger.info(f"   Price: {price:.2f}")
            self.logger.info(f"   SL: {sl:.2f}")
            self.logger.info(f"   TP: {tp:.2f}")
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                self.logger.error("❌ Order send failed - No result")
                return False
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"❌ Order failed: {result.retcode} - {result.comment}")
                return False
            
            # Success
            self.logger.info(f"\n✅ ORDER PLACED SUCCESSFULLY!")
            self.logger.info(f"   Order Ticket: {result.order}")
            if result.deal > 0:
                self.logger.info(f"   Deal Ticket: {result.deal}")
            
            # Sound alert
            if ENABLE_SOUND_ALERT:
                try:
                    import winsound
                    winsound.Beep(2500, 500)
                except:
                    pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Trade execution failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def send_final_alert(self, decision, fvg_data=None):
        """Send final trading recommendation"""
        self.logger.info("\n" + "="*60)
        self.logger.info("🚨 TRADING RECOMMENDATION")
        self.logger.info("="*60)
        self.logger.info(f"⏰ Time: {decision['timestamp']}")
        self.logger.info(f"🎯 ACTION: {decision['action']}")
        self.logger.info(f"📊 Confidence: {decision.get('buy_votes', 0) if decision['action'] == 'BUY' else decision.get('sell_votes', 0)}/{decision.get('total_signals', 0)} signals")
        self.logger.info("="*60)
        
        # Execute trade if enabled
        if decision['action'] in ['BUY', 'SELL']:
            trade_executed = self.execute_trade(decision, fvg_data)
            
            if not trade_executed and ENABLE_AUTO_TRADING:
                self.logger.warning("⚠️ Trade execution failed - check logs")
        
        # Sound alert for BUY/SELL (only if not auto-trading or trade failed)
        if decision['action'] in ['BUY', 'SELL'] and ENABLE_SOUND_ALERT and not ENABLE_AUTO_TRADING:
            try:
                import winsound
                winsound.Beep(2000, 1000)  # 2000 Hz for 1 second
            except:
                pass
    
    def daily_update(self):
        """Daily update: fetch news and update all systems"""
        self.logger.info("\n" + "="*60)
        self.logger.info("🔄 DAILY SYSTEM UPDATE")
        self.logger.info("="*60)
        
        try:
            # Fetch news
            self.fetch_daily_news()
            
            # Update FVG system (it will handle its own daily update)
            from detect_FVG.Run_FVG import FVGTradingSystem
            fvg_system = FVGTradingSystem()
            fvg_system.full_data_update()
            
            # Update price predictor (it will handle its own daily update)
            from PredictNextPrice.Run_PricePredictor import PricePredictionSystem
            price_system = PricePredictionSystem()
            price_system.full_daily_update()
            
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
    
    def run_trading_cycle(self):
        """Run one complete trading cycle"""
        self.logger.info("\n" + "="*80)
        self.logger.info(f"🔄 TRADING CYCLE START - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("="*80)
        
        # Step 1: Check news
        if self.check_news_window():
            self.logger.warning("⏭️ SKIPPING CYCLE - High-impact news within window")
            return
        
        # Step 2: Run FVG analysis
        fvg_result = self.run_fvg_analysis()
        
        # PATH A: Strong FVG Area (Original Logic)
        if fvg_result and fvg_result['is_strong']:
            self.logger.info("✅ PATH A: Strong FVG detected - Using FVG + Price + Volume/Momentum")
            
            # Step 3: Get price prediction
            price_pred = self.predict_next_price()
            
            # Step 4: Get volume & momentum votes
            vm_votes = self.get_volume_momentum_votes()
            
            # Step 5: Make final decision
            decision = self.make_final_decision(fvg_result, price_pred, vm_votes)
            
            if decision and decision['action'] in ['BUY', 'SELL']:
                # Pass FVG data for SL/TP calculation
                self.send_final_alert(decision, fvg_data=fvg_result)
            else:
                self.logger.info("ℹ️ No clear trading signal - WAIT")
        
        # PATH B: Weak/No FVG Area (Fallback to Full Voting)
        else:
            self.logger.info("⚠️ PATH B: No strong FVG - Using Full Voting System (7 Models)")
            
            # Get full voting recommendation
            voting_result = self.get_full_voting_recommendation()
            
            if not voting_result:
                self.logger.info("ℹ️ Full voting not available - WAIT")
                return
            
            # Get price prediction for validation
            price_pred = self.predict_next_price()
            
            if not price_pred:
                self.logger.info("ℹ️ Price prediction not available - WAIT")
                return
            
            # Validate: voting recommendation must match price direction
            voting_action = voting_result['recommendation'].upper()
            price_direction = price_pred['direction']
            
            self.logger.info(f"\n🔍 Validation Check:")
            self.logger.info(f"   Voting Recommendation: {voting_action}")
            self.logger.info(f"   Price Direction: {price_direction}")
            
            # Check if they match
            is_valid = False
            if voting_action == 'BUY' and price_direction == 'UP':
                is_valid = True
            elif voting_action == 'SELL' and price_direction == 'DOWN':
                is_valid = True
            
            if is_valid:
                self.logger.info("✅ VALIDATED: Voting and Price Prediction MATCH!")
                
                decision = {
                    'action': voting_action,
                    'buy_votes': 1 if voting_action == 'BUY' else 0,
                    'sell_votes': 1 if voting_action == 'SELL' else 0,
                    'total_signals': 2,
                    'confidence': voting_result['confidence'],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                self.send_final_alert(decision)
            else:
                self.logger.warning("❌ MISMATCH: Voting and Price Prediction do NOT match - WAIT")
    
    def run_continuous(self):
        """Main continuous monitoring loop"""
        self.logger.info("\n" + "="*60)
        self.logger.info("🚀 INTEGRATED TRADING SYSTEM STARTED")
        self.logger.info("="*60)
        self.logger.info(f"⏰ Daily Update Time: {DAILY_UPDATE_HOUR}:00 AM")
        self.logger.info(f"🔄 Trading Cycle: Every {CHECK_INTERVAL_MINUTES} minutes")
        self.logger.info(f"📰 News Window: ±{NEWS_WINDOW_MINUTES} minutes")
        self.logger.info("="*60)
        
        # Initialize MT5
        if not self.initialize_mt5():
            self.logger.error("❌ Cannot start without MT5 connection")
            return
        
        # Run initial daily update
        self.daily_update()
        
        try:
            while True:
                # Check if daily update is needed
                if self.should_run_daily_update():
                    self.daily_update()
                
                # Run trading cycle
                self.run_trading_cycle()
                
                # Wait for next cycle
                self.logger.info(f"\n💤 Sleeping for {CHECK_INTERVAL_MINUTES} minutes...")
                time.sleep(CHECK_INTERVAL_MINUTES * 60)
                
        except KeyboardInterrupt:
            self.logger.info("\n⚠️ System stopped by user")
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
    system = IntegratedTradingSystem()
    system.run_continuous()


if __name__ == "__main__":
    main()
