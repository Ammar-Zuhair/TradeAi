"""
Run_System_Dual.py - Dual Account Real-Time Trading System
===========================================================

ARCHITECTURE:
  Thread 1: Data Updater (every 15 min) - loads FVG zones
  Thread 2: Advanced Strategy Monitor (Account 1)
  Thread 3: Simple Strategy Monitor (Account 2)
  Thread 4: Voting Strategy Monitor (Account 3)

ADVANCED STRATEGY:
  - FVG strong (score >= 60%) + H1/M15 trend
  - Price prediction + Volume/Momentum + Voting
  - Execute on retest, zone marked as used

SIMPLE STRATEGY:
  - FVG strong (score >= 60%) + H1/M15 trend ONLY
  - Execute on retest, zone marked as used

VOTING STRATEGY:
  - Full Voting System (7 Models) + Price Prediction
  - Independent of FVG zones
  - Execute when Voting matches Price Prediction
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import joblib
import os
import sys
import threading
import time
import math
import warnings
import logging
import logging
import csv
from datetime import datetime, timedelta
from tensorflow import keras




from BackEnd import database

try:
    from env_loader import Config
except ImportError:
    print("Error: env_loader.py not found!")
    sys.exit(1)

warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'detect_FVG'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'PredictNextPrice'))
# Add BackEnd to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'BackEnd'))

from database import SessionLocal
from account import Account
from trade import Trade
from user import User
from security import decrypt
from sqlalchemy.orm import Session

# ==================== CONFIG ====================
SYMBOL = Config.SYMBOL
FVG_STRONG_THRESHOLD = Config.FVG_STRONG_THRESHOLD
RISK_PERCENTAGE = Config.RISK_PERCENTAGE
CHECK_INTERVAL_MINUTES = Config.CHECK_INTERVAL_MINUTES
REALTIME_CHECK_SECONDS = Config.REALTIME_CHECK_SECONDS
NEWS_WINDOW_MINUTES = Config.NEWS_WINDOW_MINUTES
ENABLE_SOUND_ALERT = Config.ENABLE_SOUND_ALERT
ENABLE_LOG_FILE = Config.ENABLE_LOG_FILE
ENABLE_AUTO_TRADING = Config.ENABLE_AUTO_TRADING

MODELS_DIR = 'models'
SCALERS_DIR = 'scalers'
MIN_LOT_SIZE = 0.01
MAX_LOT_SIZE = 10.0


# ==================== SHARED STATE & CONTEXT ====================
class MT5Context:
    def __init__(self):
        self.lock = threading.Lock()
        
    def execute(self, credentials, func, *args, **kwargs):
        """
        Execute a function within a strict MT5 account context.
        Acquires lock -> Initializes specific account -> Runs function -> Shuts down -> Releases lock.
        """
        with self.lock:
            try:
                # Initialize with specific account
                if not mt5.initialize(
                    login=credentials['login'],
                    password=credentials['password'],
                    server=credentials['server']
                ):
                    print(f"❌ MT5 Context Init Failed for {credentials.get('login')}: {mt5.last_error()}")
                    return None
                
                # Execute the function
                return func(*args, **kwargs)
                
            except Exception as e:
                print(f"❌ MT5 Context Error: {e}")
                import traceback
                traceback.print_exc()
                return None
            finally:
                # Always shutdown to ensure no account leakage
                mt5.shutdown()

class SharedState:
    def __init__(self):
        self.lock = threading.Lock()
        self.active_fvg_zones = []
        self.last_update_time = None
        self.should_stop = threading.Event()
        
    def update_zones(self, zones):
        with self.lock:
            self.active_fvg_zones = zones
            self.last_update_time = datetime.now()
            
    def get_zones(self):
        with self.lock:
            return self.active_fvg_zones.copy()
    
    def stop_all(self):
        self.should_stop.set()


# ==================== BASE MONITOR ====================
class AccountMonitor:
    def __init__(self, account_name, credentials, shared_state, strategy_type, mt5_context):
        self.account_name = account_name
        self.credentials = credentials
        self.shared_state = shared_state
        self.strategy_type = strategy_type
        self.mt5_context = mt5_context
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.models_dir = os.path.join(self.script_dir, MODELS_DIR)
        self.scalers_dir = os.path.join(self.script_dir, SCALERS_DIR)
        
        self.used_zones = set()
        
        self._setup_logging()
        
    def _setup_logging(self):
        log_file = f'trading_{self.strategy_type}.log'
        self.logger = logging.getLogger(f'{self.account_name}_{self.strategy_type}')
        self.logger.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(f'[{self.account_name}] %(asctime)s - %(message)s')
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        if ENABLE_LOG_FILE:
            file_handler = logging.FileHandler(os.path.join(self.script_dir, log_file), encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(console_format)
            self.logger.addHandler(file_handler)

    def _print_account_info(self):
        """Helper to print account info at startup"""
        try:
            account_info = mt5.account_info()
            if account_info:
                self.logger.info(f"📊 Account Connected: {account_info.login}")
                self.logger.info(f"   Balance: ${account_info.balance:.2f}")
                self.logger.info(f"   Server: {account_info.server}")
                return True
        except Exception as e:
            self.logger.error(f"❌ Failed to get account info: {e}")
        return False
    
    # Removed initialize_mt5 and shutdown_mt5 as they are handled by MT5Context
    
    def get_current_price(self):
        tick = mt5.symbol_info_tick(SYMBOL)
        return (tick.bid, tick.ask) if tick else (None, None)
    
    def is_price_in_zone(self, price, zone):
        fvg_bottom = zone.get('fvg_bottom')
        fvg_top = zone.get('fvg_top')
        if fvg_bottom is None or fvg_top is None:
            return False
        return fvg_bottom <= price <= fvg_top
    
    def mark_zone_as_used(self, zone):
        zone_id = str(zone.get('fvg_time', zone.get('timestamp')))
        self.used_zones.add(zone_id)
        self.logger.info(f"🔒 Zone used: {zone_id}")
    
    def is_zone_used(self, zone):
        zone_id = str(zone.get('fvg_time', zone.get('timestamp')))
        return zone_id in self.used_zones
    
    def calculate_lot_size(self, sl_distance_points):
        try:
            account_info = mt5.account_info()
            symbol_info = mt5.symbol_info(SYMBOL)
            if not account_info or not symbol_info:
                return MIN_LOT_SIZE
            
            balance = account_info.balance
            risk_amount = balance * (RISK_PERCENTAGE / 100)
            contract_size = symbol_info.trade_contract_size
            pip_value_per_lot = contract_size * 0.01
            sl_distance_pips = sl_distance_points / 10
            
            if sl_distance_pips <= 0:
                return MIN_LOT_SIZE
            
            lot_size = risk_amount / (pip_value_per_lot * sl_distance_pips)
            lot_size = max(MIN_LOT_SIZE, min(MAX_LOT_SIZE, lot_size))
            lot_size = math.floor(lot_size * 100) / 100
            return lot_size
        except:
            return MIN_LOT_SIZE
    
    def _log_trade_attempt_csv(self, action, price, sl, tp, lot_size, strategy_name):
        try:
            csv_file = os.path.join(self.script_dir, 'trade_attempts.csv')
            file_exists = os.path.exists(csv_file)
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['Time', 'Strategy', 'Symbol', 'Action', 'Price', 'SL', 'TP', 'LotSize'])
                
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    strategy_name,
                    SYMBOL,
                    action,
                    price,
                    sl,
                    tp,
                    lot_size
                ])
            self.logger.info(f"📝 Trade attempt logged to CSV: {action} @ {price}")
        except Exception as e:
            self.logger.error(f"❌ Failed to log trade attempt to CSV: {e}")

    def execute_fvg_trade(self, zone, action):
        if not ENABLE_AUTO_TRADING:
            self.logger.info(f"ℹ️ Recommendation: {action} (Auto-trading OFF)")
            return False
        
        # Note: This method is expected to be called WITHIN an MT5Context.execute block
        # so we assume MT5 is initialized and on the correct account.
        
        try:
            symbol_info = mt5.symbol_info(SYMBOL)
            tick = mt5.symbol_info_tick(SYMBOL)
            if not symbol_info or not tick:
                return False
            
            current_bid, current_ask = tick.bid, tick.ask
            point = symbol_info.point
            
            fvg_bottom = zone['fvg_bottom']
            fvg_top = zone['fvg_top']
            fvg_size = zone['fvg_size']
            
            if action == 'BUY':
                entry_price = fvg_bottom + 0.5
                sl = fvg_bottom - 1.0 + (fvg_size * 0.1)
                risk = entry_price - sl
                tp = entry_price + (risk * 5.0)
                price = current_ask
                order_type = mt5.ORDER_TYPE_BUY
            else:
                entry_price = fvg_top - 0.5
                sl = fvg_top + 1.0
                risk = sl - entry_price
                tp = entry_price - (risk * 5.0)
                price = current_bid
                order_type = mt5.ORDER_TYPE_SELL
            
            sl_distance_mt5_points = abs(sl - price) / point
            lot_size = self.calculate_lot_size(sl_distance_mt5_points)
            
            # Log attempt before execution
            self._log_trade_attempt_csv(action, price, sl, tp, lot_size, f"{self.strategy_type.upper()}_FVG")
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234000,
                "comment": f"{self.strategy_type.upper()}_FVG",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            self.logger.info(f"\n📋 {action} | Entry: {price:.2f} | SL: {sl:.2f} | TP: {tp:.2f} | Lot: {lot_size}")
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"✅ ORDER EXECUTED! Ticket: {result.order}")
                self.mark_zone_as_used(zone)
                
                # Log trade to Database
                try:
                    db: Session = SessionLocal()
                    # Find account ID based on login
                    account = db.query(Account).filter(Account.AccountLoginNumber == self.credentials['login']).first()
                    if account:
                        new_trade = Trade(
                            TradeID=result.order, # Use Ticket as ID
                            AccountID=account.AccountID,
                            # TradeTicket removed
                            TradeType=action,
                            TradeAsset=SYMBOL,
                            TradeLotsize=lot_size,
                            TradeOpenPrice=result.price,
                            TradeOpenTime=datetime.now(),
                            TradeStatus='Open'
                        )
                        db.add(new_trade)
                        db.commit()
                        self.logger.info(f"💾 Trade saved to DB (ID: {new_trade.TradeID}, Ticket: {result.order})")
                        
                        # Send Notification
                        try:
                            user = db.query(User).filter(User.UserID == account.UserID).first()
                            if user and user.IsNotificationsEnabled and user.PushToken:
                                from utils.notifications import send_push_notification
                                send_push_notification(
                                    token=user.PushToken,
                                    title="New Auto Trade 🤖",
                                    body=f"{action} {SYMBOL} @ {result.price}",
                                    data={"trade_id": new_trade.TradeID}
                                )
                        except Exception as e:
                            self.logger.error(f"⚠️ Failed to send notification: {e}")
                    else:
                        self.logger.error(f"❌ Account not found in DB for login: {self.credentials['login']}")

                    db.close()
                except Exception as e:
                    self.logger.error(f"❌ Failed to save trade to DB: {e}")

                if ENABLE_SOUND_ALERT:
                    try:
                        import winsound
                        winsound.Beep(2500, 500)
                    except:
                        pass
                return True
            else:
                self.logger.error(f"❌ Order failed: {result.retcode} ({result.comment})")
                return False
        except Exception as e:
            self.logger.error(f"❌ Trade execution failed: {e}")
            return False
    
    def run(self):
        raise NotImplementedError()


# ==================== ADVANCED STRATEGY ====================
class AdvancedStrategyMonitor(AccountMonitor):
    def __init__(self, credentials, shared_state, mt5_context):
        super().__init__('ADV', credentials, shared_state, 'advanced', mt5_context)
    
    def check_advanced_conditions(self, zone, bid, ask):
        """Full conditions: FVG + Price Prediction + Voting"""
        direction = zone.get('direction')
        if not direction or direction not in ['BUY', 'SELL']:
            return False
        
        # 1. Check Zone Retest (Basic FVG)
        price = bid if direction == 'SELL' else ask
        if not self.is_price_in_zone(price, zone):
            return False
            
        score = zone.get('score', 0)
        if score < FVG_STRONG_THRESHOLD:
            return False

        self.logger.info(f"\n🔍 Analyzing Advanced Conditions for {direction} at {price}...")

        # 2. Price Prediction (Short-term trend)
        try:
            from PredictNextPrice.Run_PricePredictor import PricePredictionSystem
            price_system = PricePredictionSystem()
            prediction = price_system.predict_next_price()
            
            if not prediction:
                self.logger.info("   ❌ Price prediction unavailable")
                return False
                
            pred_direction = prediction['direction'] # UP / DOWN
            
            # Map UP/DOWN to BUY/SELL
            is_pred_valid = (direction == 'BUY' and pred_direction == 'UP') or \
                            (direction == 'SELL' and pred_direction == 'DOWN')
                            
            if not is_pred_valid:
                self.logger.info(f"   ❌ Prediction Mismatch: FVG={direction}, Pred={pred_direction}")
                return False
                
            self.logger.info(f"   ✅ Prediction Match: {pred_direction}")
            
        except Exception as e:
            self.logger.error(f"   ⚠️ Prediction check failed: {e}")
            return False

        # 3. Voting System (Market Sentiment)
        try:
            from getDataAndVoting import MarketPredictionSystem
            voting_system = MarketPredictionSystem(
                symbol=SYMBOL,
                models_dir=self.models_dir,
                scalers_dir=self.scalers_dir
            )
            
            # Initialize MT5 if needed (we are in context, but class might need init)
            if not voting_system.mt5_initialized:
                voting_system.initialize_mt5()
                
            voting_system.fetch_market_data(timeframe=mt5.TIMEFRAME_M15, days=7)
            voting_result = voting_system.get_final_recommendation()
            
            if not voting_result:
                self.logger.info("   ❌ Voting unavailable")
                return False
                
            vote_recommendation = voting_result['recommendation'].upper() # BUY / SELL
            
            if vote_recommendation != direction:
                self.logger.info(f"   ❌ Voting Mismatch: FVG={direction}, Vote={vote_recommendation}")
                return False
                
            self.logger.info(f"   ✅ Voting Match: {vote_recommendation} ({voting_result['confidence']:.1%})")

        except Exception as e:
            self.logger.error(f"   ⚠️ Voting check failed: {e}")
            return False

        # All conditions met
        self.logger.info("   🚀 ALL ADVANCED CONDITIONS MET!")
        return True
    
    def run(self):
        self.logger.info("\n" + "="*60)
        self.logger.info("🚀 ADVANCED STRATEGY STARTED")
        self.logger.info("="*60)
        
        # Initial Account Check
        self.mt5_context.execute(self.credentials, self._print_account_info)
        
        def logic_step():
            # This function runs inside the strict MT5 context
            try:
                # 1. Get Price
                bid, ask = self.get_current_price()
                if not bid or not ask:
                    return
                
                # 2. Check Zones
                zones = self.shared_state.get_zones()
                if zones:
                    for zone in zones:
                        if self.is_zone_used(zone):
                            continue
                        
                        direction = zone.get('direction')
                        if self.check_advanced_conditions(zone, bid, ask):
                            self.logger.info(f"\n✅ ADVANCED TRIGGER | Zone: {zone.get('fvg_time')} | {direction}")
                            if self.execute_fvg_trade(zone, direction):
                                break
            except Exception as e:
                self.logger.error(f"Logic step error: {e}")

        try:
            while not self.shared_state.should_stop.is_set():
                # Execute the logic step within the strict context
                self.mt5_context.execute(self.credentials, logic_step)
                
                time.sleep(REALTIME_CHECK_SECONDS)
        except KeyboardInterrupt:
            self.logger.info("\n⚠️ Stopped by user")
        except Exception as e:
            self.logger.error(f"\n❌ Error: {e}")


# ==================== SIMPLE STRATEGY ====================
class SimpleStrategyMonitor(AccountMonitor):
    def __init__(self, credentials, shared_state, mt5_context):
        super().__init__('SIMPLE', credentials, shared_state, 'simple', mt5_context)
    
    def check_simple_conditions(self, zone, bid, ask):
        """Simple: FVG strong + trend ONLY"""
        direction = zone.get('direction')
        if not direction or direction not in ['BUY', 'SELL']:
            return False
        
        score = zone.get('score', 0)
        if score < FVG_STRONG_THRESHOLD:
            return False
        
        price = bid if direction == 'SELL' else ask
        if not self.is_price_in_zone(price, zone):
            return False
        
        return True
    
    def run(self):
        self.logger.info("\n" + "="*60)
        self.logger.info("🚀 SIMPLE STRATEGY STARTED")
        self.logger.info("="*60)
        
        # Initial Account Check
        self.mt5_context.execute(self.credentials, self._print_account_info)
        
        def logic_step():
            try:
                bid, ask = self.get_current_price()
                if not bid or not ask:
                    return

                zones = self.shared_state.get_zones()
                if zones:
                    for zone in zones:
                        if self.is_zone_used(zone):
                            continue
                        
                        direction = zone.get('direction')
                        if self.check_simple_conditions(zone, bid, ask):
                            self.logger.info(f"\n✅ SIMPLE TRIGGER | Zone: {zone.get('fvg_time')} | {direction}")
                            if self.execute_fvg_trade(zone, direction):
                                break
            except Exception as e:
                self.logger.error(f"Logic step error: {e}")
        
        try:
            while not self.shared_state.should_stop.is_set():
                self.mt5_context.execute(self.credentials, logic_step)
                time.sleep(REALTIME_CHECK_SECONDS)
        except KeyboardInterrupt:
            self.logger.info("\n⚠️ Stopped by user")
        except Exception as e:
            self.logger.error(f"\n❌ Error: {e}")


# ==================== VOTING STRATEGY ====================
class VotingStrategyMonitor(AccountMonitor):
    def __init__(self, credentials, shared_state, mt5_context):
        super().__init__('VOTING', credentials, shared_state, 'voting', mt5_context)
        self.last_check_time = datetime.now()
        
    def get_full_voting_recommendation(self):
        """Get recommendation from all 7 models"""
        self.logger.info("\n🗳️ Running Full Voting System (7 Models)...")
        
        try:
            from getDataAndVoting import MarketPredictionSystem
            
            voting_system = MarketPredictionSystem(
                symbol=SYMBOL,
                models_dir=self.models_dir,
                scalers_dir=self.scalers_dir
            )
            
            # Initialize MT5 if needed (using our connection)
            # Note: We are already inside MT5Context, so mt5 is initialized.
            # We call this just to satisfy the class state if it checks self.mt5_initialized
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
            return None

    def predict_next_price(self):
        """Predict next 15-min close price"""
        self.logger.info("\n💰 Predicting Next Price...")
        
        try:
            from PredictNextPrice.Run_PricePredictor import PricePredictionSystem
            
            price_system = PricePredictionSystem()
            
            # Get prediction
            prediction = price_system.predict_next_price()
            
            if prediction:
                self.logger.info(f"✅ Price Prediction:")
                self.logger.info(f"   Direction: {prediction['direction']}")
                return prediction
            else:
                self.logger.info("ℹ️ Price prediction not available")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Price prediction failed: {e}")
            return None

    def calculate_dynamic_sl_tp(self, action, current_price):
        """
        Calculate dynamic SL/TP based on last 10 candles
        
        Args:
            action: 'BUY' or 'SELL'
            current_price: Current entry price
            
        Returns:
            tuple: (sl_price, tp_price) or (None, None) if calculation fails
        """
        try:
            # Fetch last 10 candles (M15 timeframe)
            rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M15, 0, 10)
            
            if rates is None or len(rates) < 10:
                self.logger.warning("⚠️ Could not fetch enough candles for dynamic SL/TP, using fallback")
                return None, None
            
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(rates)
            
            # Buffer distance (configurable, default 5 points = 0.5 pips for gold)
            BUFFER_POINTS = 5
            symbol_info = mt5.symbol_info(SYMBOL)
            point = symbol_info.point if symbol_info else 0.01
            buffer = BUFFER_POINTS * point
            
            if action == 'BUY':
                # For BUY: SL below lowest low of last 10 candles
                lowest_low = df['low'].min()
                sl = lowest_low - buffer
                
                # TP = 2x SL distance
                sl_distance = current_price - sl
                tp = current_price + (sl_distance * 2.0)
                
                self.logger.info(f"📊 Dynamic SL/TP (BUY):")
                self.logger.info(f"   Lowest Low (10 candles): {lowest_low:.2f}")
                self.logger.info(f"   SL: {sl:.2f} (buffer: {buffer:.2f})")
                self.logger.info(f"   TP: {tp:.2f} (2x SL distance)")
                
            else:  # SELL
                # For SELL: SL above highest high of last 10 candles
                highest_high = df['high'].max()
                sl = highest_high + buffer
                
                # TP = 2x SL distance
                sl_distance = sl - current_price
                tp = current_price - (sl_distance * 2.0)
                
                self.logger.info(f"📊 Dynamic SL/TP (SELL):")
                self.logger.info(f"   Highest High (10 candles): {highest_high:.2f}")
                self.logger.info(f"   SL: {sl:.2f} (buffer: {buffer:.2f})")
                self.logger.info(f"   TP: {tp:.2f} (2x SL distance)")
            
            return sl, tp
            
        except Exception as e:
            self.logger.error(f"❌ Dynamic SL/TP calculation failed: {e}")
            return None, None

    def execute_voting_trade(self, action):
        if not ENABLE_AUTO_TRADING:
            self.logger.info(f"ℹ️ Recommendation: {action} (Auto-trading OFF)")
            return False
        
        # Assumes MT5Context is active
        try:
            symbol_info = mt5.symbol_info(SYMBOL)
            tick = mt5.symbol_info_tick(SYMBOL)
            if not symbol_info or not tick:
                return False
                
            current_bid, current_ask = tick.bid, tick.ask
            point = symbol_info.point
            
            # Determine entry price based on action
            if action == 'BUY':
                price = current_ask
                order_type = mt5.ORDER_TYPE_BUY
            else:
                price = current_bid
                order_type = mt5.ORDER_TYPE_SELL
            
            # Calculate dynamic SL/TP based on last 10 candles
            sl, tp = self.calculate_dynamic_sl_tp(action, price)
            
            # Fallback to fixed SL/TP if dynamic calculation fails
            if sl is None or tp is None:
                self.logger.warning("⚠️ Using fallback fixed SL/TP (30/60 pips)")
                FIXED_SL_PIPS = 30
                FIXED_TP_PIPS = 60  # 1:2 Ratio
                
                if action == 'BUY':
                    sl = price - (FIXED_SL_PIPS * 10 * point)
                    tp = price + (FIXED_TP_PIPS * 10 * point)
                else:
                    sl = price + (FIXED_SL_PIPS * 10 * point)
                    tp = price - (FIXED_TP_PIPS * 10 * point)
                
            sl_distance_mt5_points = abs(sl - price) / point
            lot_size = self.calculate_lot_size(sl_distance_mt5_points)
            
            # Log attempt before execution
            self._log_trade_attempt_csv(action, price, sl, tp, lot_size, "VOTING_ONLY")
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234001, # Different magic number
                "comment": "VOTING_ONLY",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            self.logger.info(f"\n📋 {action} | Entry: {price:.2f} | SL: {sl:.2f} | TP: {tp:.2f} | Lot: {lot_size}")
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"✅ ORDER EXECUTED! Ticket: {result.order}")
                
                # Log trade to Database
                try:
                    db: Session = SessionLocal()
                    account = db.query(Account).filter(Account.AccountLoginNumber == self.credentials['login']).first()
                    if account:
                        new_trade = Trade(
                            TradeID=result.order, # Use Ticket as ID
                            AccountID=account.AccountID,
                            # TradeTicket removed
                            TradeType=action,
                            TradeAsset=SYMBOL,
                            TradeLotsize=lot_size,
                            TradeOpenPrice=result.price,
                            TradeOpenTime=datetime.now(),
                            TradeStatus='Open'
                        )
                        db.add(new_trade)
                        db.commit()
                        self.logger.info(f"💾 Trade saved to DB (ID: {new_trade.TradeID}, Ticket: {result.order})")
                    db.close()
                except Exception as e:
                    self.logger.error(f"❌ Failed to save trade to DB: {e}")

                if ENABLE_SOUND_ALERT:
                    try:
                        import winsound
                        winsound.Beep(2000, 500)
                    except:
                        pass
                return True
            else:
                self.logger.error(f"❌ Order failed: {result.retcode} ({result.comment})")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Trade execution failed: {e}")
            return False

    def run(self):
        self.logger.info("\n" + "="*60)
        self.logger.info("🚀 VOTING STRATEGY STARTED")
        self.logger.info("="*60)
        
        # Initial Account Check
        self.mt5_context.execute(self.credentials, self._print_account_info)
        
        def logic_step():
            try:
                # Check for open positions first
                positions = mt5.positions_get(symbol=SYMBOL)
                if positions and len(positions) > 0:
                    # Skip if already in trade
                    return
                
                # Get full voting recommendation
                voting_result = self.get_full_voting_recommendation()
                
                if voting_result:
                    # Get price prediction for validation
                    price_pred = self.predict_next_price()
                    
                    if price_pred:
                        voting_action = voting_result['recommendation'].upper()
                        price_direction = price_pred['direction']
                        
                        is_valid = False
                        if voting_action == 'BUY' and price_direction == 'UP':
                            is_valid = True
                        elif voting_action == 'SELL' and price_direction == 'DOWN':
                            is_valid = True
                            
                        if is_valid:
                            self.logger.info(f"\n✅ VALIDATED: Voting ({voting_action}) matches Price ({price_direction})")
                            if self.execute_voting_trade(voting_action):
                                # Sleep for a while to avoid duplicate trades on same signal
                                # We can't sleep inside the lock for 15 mins!
                                # So we return a flag or handle sleep outside
                                return "SLEEP"
                        else:
                            self.logger.info(f"ℹ️ Mismatch: Voting {voting_action} vs Price {price_direction}")
            except Exception as e:
                self.logger.error(f"Voting logic error: {e}")
            return None

        try:
            while not self.shared_state.should_stop.is_set():
                result = self.mt5_context.execute(self.credentials, logic_step)
                
                if result == "SLEEP":
                     # Sleep 15 minutes outside the lock
                    for _ in range(15 * 60):
                        if self.shared_state.should_stop.is_set():
                            break
                        time.sleep(1)
                else:
                    time.sleep(REALTIME_CHECK_SECONDS)
                
        except KeyboardInterrupt:
            self.logger.info("\n⚠️ Stopped by user")
        except Exception as e:
            self.logger.error(f"\n❌ Error: {e}")



# ==================== DATA UPDATER ====================
class DataUpdater:
    def __init__(self, shared_state, mt5_context, credentials):
        self.shared_state = shared_state
        self.mt5_context = mt5_context
        self.credentials = credentials
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.fvg_dir = os.path.join(self.script_dir, 'detect_FVG')
        self.fvg_csv_path = os.path.join(self.fvg_dir, 'fvg_analysis_XAUUSD_M15_4H.csv')
        
        self.logger = logging.getLogger('DataUpdater')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('[DATA] %(asctime)s - %(message)s'))
        self.logger.addHandler(handler)
        
        self.model_path = os.path.join(self.fvg_dir, 'fvg_strong_classifier.joblib')
        self.model = None
        self.load_model()
        
    def load_model(self):
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.logger.info("✅ FVG Model loaded")
            else:
                self.logger.warning("⚠️ FVG Model not found")
        except Exception as e:
            self.logger.error(f"❌ Failed to load model: {e}")
    
    def run_fvg_analysis(self):
        """Run FVG analysis to update data"""
        try:
            self.logger.info("🔄 Running FVG analysis...")
            
            # Import and run FVG system
            from detect_FVG.Run_FVG import FVGTradingSystem
            
            fvg_system = FVGTradingSystem()
            
            # Note: We assume we are inside MT5Context here
            # FVGTradingSystem.initialize_mt5() will be called but should be fine
            
            # Run full data update
            fvg_system.full_data_update()
            
            # We do NOT call fvg_system.shutdown_mt5() here because MT5Context handles it
            # But FVGTradingSystem might call it internally? 
            # Checked Run_FVG.py: full_data_update() does NOT call shutdown_mt5().
            # It just calls _fetch_and_update_data, _run_fvg_analysis, _train_classifier.
            # So we are safe.
            
            self.logger.info("✅ FVG analysis completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ FVG analysis failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def load_fvg_zones(self):
        try:
            if not os.path.exists(self.fvg_csv_path):
                self.logger.warning("⚠️ FVG file not found - will run analysis")
                return []
            
            fvg_data = pd.read_csv(self.fvg_csv_path)
            if len(fvg_data) == 0:
                return []
            
            zones = []
            for _, row in fvg_data.tail(10).iterrows():
                # Calculate score if model exists
                score = 50
                if self.model:
                    try:
                        features = self._prepare_features(row)
                        # Align features with model
                        model_features = self.model.booster_.feature_name()
                        features_aligned = features.reindex(columns=model_features, fill_value=0)
                        
                        probability = self.model.predict_proba(features_aligned)[0, 1]
                        score = int(probability * 100)
                    except Exception as e:
                        self.logger.error(f"❌ Scoring failed: {e}")

                zone = {
                    'fvg_time': row['time_created'],
                    'fvg_bottom': row['fvg_bottom'],
                    'fvg_top': row['fvg_top'],
                    'fvg_size': row['fvg_size'],
                    'score': score,
                    'direction': 'BUY' if row.get('FVG_Type', '') == 'Bullish' else 'SELL',
                }
                zones.append(zone)
            
            return zones
        except Exception as e:
            self.logger.error(f"❌ Failed to load zones: {e}")
            return []

    def _prepare_features(self, fvg_row):
        """Prepare features for model prediction"""
        df = pd.DataFrame([fvg_row])
        categorical_features = ['FVG_Type', 'session', 'bias_H1']
        # Handle missing columns if any
        for col in categorical_features:
            if col not in df.columns:
                df[col] = 'N/A'
                
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

    
    def run(self):
        self.logger.info("\n" + "="*60)
        self.logger.info("🔄 DATA UPDATER STARTED")
        self.logger.info(f"   Interval: {CHECK_INTERVAL_MINUTES} min")
        self.logger.info( "   Auto FVG Analysis: ENABLED")
        self.logger.info("="*60)
        
        try:
            # Run FVG analysis on first start if file missing
            if not os.path.exists(self.fvg_csv_path):
                self.logger.info("\n📊 Initial FVG analysis...")
                self.run_fvg_analysis()
            
            while not self.shared_state.should_stop.is_set():
                # Run FVG analysis every cycle using strict context
                self.mt5_context.execute(self.credentials, self.run_fvg_analysis)
                
                # Load zones
                zones = self.load_fvg_zones()
                self.shared_state.update_zones(zones)
                self.logger.info(f"\n📊 Updated: {len(zones)} zones")
                
                # Wait for next cycle
                for _ in range(CHECK_INTERVAL_MINUTES * 60):
                    if self.shared_state.should_stop.is_set():
                        break
                    time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("\n⚠️ Stopped by user")
        except Exception as e:
            self.logger.error(f"\n❌ Error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())


# ==================== TRADE MONITOR ====================
class TradeMonitor:
    def __init__(self, mt5_context):
        self.mt5_context = mt5_context
        self.logger = logging.getLogger('TradeMonitor')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('[MONITOR] %(asctime)s - %(message)s'))
        self.logger.addHandler(handler)
        
    def check_open_trades(self):
        """Check all open trades in DB and update status"""
        try:
            db: Session = SessionLocal()
            open_trades = db.query(Trade).filter(Trade.TradeStatus == 'Open').all()
            
            if not open_trades:
                db.close()
                return

            # Group by account to minimize context switching
            trades_by_account = {}
            for trade in open_trades:
                if trade.AccountID not in trades_by_account:
                    trades_by_account[trade.AccountID] = []
                trades_by_account[trade.AccountID].append(trade)
            
            for account_id, trades in trades_by_account.items():
                account = db.query(Account).filter(Account.AccountID == account_id).first()
                if not account:
                    continue
                    
                creds = {
                    "login": account.AccountLoginNumber,
                    "password": decrypt(account.AccountLoginPassword),
                    "server": account.AccountLoginServer
                }
                
                # Execute check in MT5 context
                self.mt5_context.execute(creds, self._check_trades_for_account, trades, db)
                
            db.close()
            
        except Exception as e:
            self.logger.error(f"❌ Monitor failed: {e}")

    def _check_trades_for_account(self, trades, db):
        """Check trades for a specific account (inside MT5 context)"""
        for trade in trades:
            try:
                # TradeID is the Ticket
                ticket = trade.TradeID
                
                # Check if position exists (Open)
                positions = mt5.positions_get(ticket=ticket)
                
                if positions and len(positions) > 0:
                    # Trade is still OPEN
                    pos = positions[0]
                    trade.TradeProfitLose = pos.profit
                else:
                    # Trade is NOT in positions -> CLOSED
                    # Check history to confirm and get final profit
                    deals = mt5.history_deals_get(position=ticket)
                    
                    if deals and len(deals) > 0:
                        # Calculate total profit for this position
                        total_profit = sum(deal.profit + deal.swap + deal.commission for deal in deals)
                        
                        # Find exit time and price (last deal)
                        last_deal = deals[-1]
                        
                        trade.TradeStatus = 'Winning' if total_profit >= 0 else 'Losing'
                        trade.TradeProfitLose = total_profit
                        trade.TradeClosePrice = last_deal.price
                        trade.TradeCloseTime = datetime.fromtimestamp(last_deal.time)
                        
                        # UPDATE ACCOUNT BALANCE
                        account = db.query(Account).filter(Account.AccountID == trade.AccountID).first()
                        if account:
                            # Ensure we are working with Decimal/Float correctly
                            # AccountBalance is DECIMAL, total_profit is float from MT5
                            from decimal import Decimal
                            account.AccountBalance = account.AccountBalance + Decimal(str(total_profit))
                            self.logger.info(f"💰 Balance Updated: {account.AccountBalance} (Profit: {total_profit})")
                        
                        self.logger.info(f"✅ Trade {ticket} CLOSED. Profit: {total_profit}")
                    else:
                        # Could not find in history? Maybe just closed?
                        # Mark as Closed/Unknown or assume manual close
                        trade.TradeStatus = 'Closed'
                        self.logger.warning(f"⚠️ Trade {ticket} not found in history")
                
                db.commit()
                
            except Exception as e:
                self.logger.error(f"❌ Error checking trade {trade.TradeID}: {e}")

    def run(self):
        self.logger.info("\n" + "="*60)
        self.logger.info("👀 TRADE MONITOR STARTED")
        self.logger.info("="*60)
        
        while True:
            self.check_open_trades()
            time.sleep(1) # Check every 1 second as requested


# ==================== MAIN ====================
def main():
    print("\n" + "="*60)
    print("🤖 DUAL ACCOUNT TRADING SYSTEM (DB INTEGRATED)")
    print("="*60)
    
    # Shared state
    shared_state = SharedState()
    mt5_context = MT5Context()
    
    # Threads list
    threads = []
    
    try:
        db: Session = SessionLocal()
        accounts = db.query(Account).all()
        
        if not accounts:
            print("❌ No accounts found in database!")
            db.close()
            return

        print(f"📋 Found {len(accounts)} accounts in database.")
        
        # 1. Start Data Updater (Always runs, needs ANY valid account to fetch data)
        # We use the first available account from DB just for data fetching context
        first_acc = accounts[0]
        try:
            data_creds = {
                "login": first_acc.AccountLoginNumber,
                "password": decrypt(first_acc.AccountLoginPassword),
                "server": first_acc.AccountLoginServer
            }
            
            data_updater = DataUpdater(shared_state, mt5_context, data_creds)
            t_data = threading.Thread(target=data_updater.run, daemon=True)
            t_data.start()
            threads.append(t_data)
            print("✅ Data Updater started")
        except Exception as e:
            print(f"❌ Failed to start Data Updater: {e}")
            db.close()
            return

        # 3. Start Trade Monitor
        try:
            trade_monitor = TradeMonitor(mt5_context)
            t_monitor = threading.Thread(target=trade_monitor.run, daemon=True)
            t_monitor.start()
            threads.append(t_monitor)
            print("✅ Trade Monitor started")
        except Exception as e:
            print(f"❌ Failed to start Trade Monitor: {e}")

        # 2. Start Strategy Monitors based on Account Type
        for acc in accounts:
            try:
                creds = {
                    "login": acc.AccountLoginNumber,
                    "password": decrypt(acc.AccountLoginPassword),
                    "server": acc.AccountLoginServer
                }
                
                strategy = acc.TradingStrategy
                
                if strategy == 'All': # Advanced
                    monitor = AdvancedStrategyMonitor(creds, shared_state, mt5_context)
                    t = threading.Thread(target=monitor.run, daemon=True)
                    t.start()
                    threads.append(t)
                    print(f"✅ Started ADVANCED strategy for Account {acc.AccountLoginNumber}")
                    
                elif strategy == 'FVG + Trend': # Simple
                    monitor = SimpleStrategyMonitor(creds, shared_state, mt5_context)
                    t = threading.Thread(target=monitor.run, daemon=True)
                    t.start()
                    threads.append(t)
                    print(f"✅ Started SIMPLE strategy for Account {acc.AccountLoginNumber}")
                    
                elif strategy == 'Voting': # Voting
                    monitor = VotingStrategyMonitor(creds, shared_state, mt5_context)
                    t = threading.Thread(target=monitor.run, daemon=True)
                    t.start()
                    threads.append(t)
                    print(f"✅ Started VOTING strategy for Account {acc.AccountLoginNumber}")
                    
                else:
                    print(f"ℹ️ Account {acc.AccountLoginNumber} has unknown strategy '{strategy}' - Skipping")
                    
            except Exception as e:
                print(f"❌ Failed to start thread for account {acc.AccountLoginNumber}: {e}")

        db.close()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping system...")
        shared_state.stop_all()
        sys.exit(0)
    except Exception as e:
        print(f"❌ System Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()