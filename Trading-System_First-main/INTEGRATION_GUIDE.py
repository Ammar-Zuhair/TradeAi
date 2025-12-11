# ==================== CRITICAL UPDATES FOR DATABASE INTEGRATION ====================
# This file contains the necessary changes to integrate Run_System_Dual.py with the new database schema
# 
# CHANGES REQUIRED:
# 1. Import account_helper functions
# 2. Update trade logging to use Integer enums (TradeType: 1=Buy, 2=Sell)
# 3. Use TradingPairID instead of TradeAsset
# 4. Get account symbol from mapping
#
# ==================== IMPLEMENTATION ====================

"""
Add these imports at the top of Run_System_Dual.py (after line 66):
"""

# Add after: from security import decrypt
from utils.account_helper import (
    get_account_trading_info,
    get_account_symbol,
    get_trading_pair_id,
    save_trade_to_db,
    update_trade_close
)
from models.enums import TradeTypeEnum

"""
Replace the execute_fvg_trade method (lines 414-536) with this updated version:
"""

def execute_fvg_trade_UPDATED(self, zone, action):
    """
    Updated version that uses new database schema with Integer enums and TradingPairID
    """
    if not ENABLE_AUTO_TRADING:
        self.logger.info(f"ℹ️ Recommendation: {action} (Auto-trading OFF)")
        return False
    
    try:
        # Get account info to find the correct symbol for this user
        account_info = get_account_trading_info(self.account_id)
        
        if not account_info:
            self.logger.error("❌ Failed to get account info")
            return False
        
        # Get the actual symbol used in this account
        # SYMBOL is our standardized pair name (e.g., 'GOLD')
        user_symbol = account_info['symbol_mappings'].get(SYMBOL)
        
        if not user_symbol:
            self.logger.error(f"❌ No symbol mapping found for {SYMBOL}")
            return False
        
        self.logger.info(f"📍 Using symbol: {user_symbol} (mapped from {SYMBOL})")
        
        symbol_info = mt5.symbol_info(user_symbol)
        tick = mt5.symbol_info_tick(user_symbol)
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
            trade_type_int = TradeTypeEnum.BUY  # 1
        else:
            entry_price = fvg_top - 0.5
            sl = fvg_top + 1.0
            risk = sl - entry_price
            tp = entry_price - (risk * 5.0)
            price = current_bid
            order_type = mt5.ORDER_TYPE_SELL
            trade_type_int = TradeTypeEnum.SELL  # 2
        
        sl_distance_mt5_points = abs(sl - price) / point
        lot_size = self.calculate_lot_size(sl_distance_mt5_points)
        
        # Log attempt before execution
        self._log_trade_attempt_csv(action, price, sl, tp, lot_size, f"{self.strategy_type.upper()}_FVG")
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": user_symbol,  # ✅ Use user's actual symbol
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
            
            # Save trade to database using new schema
            success = save_trade_to_db(
                trade_id=result.order,
                account_id=self.account_id,
                trade_type=trade_type_int,  # ✅ Integer: 1 or 2
                our_pair_name=SYMBOL,  # ✅ Our standardized name (e.g., 'GOLD')
                lot_size=lot_size,
                open_price=result.price,
                open_time=datetime.now()
            )
            
            if success:
                self.logger.info(f"💾 Trade saved to DB")
                
                # Send Notification
                try:
                    db: Session = SessionLocal()
                    account = db.query(Account).filter(Account.AccountID == self.account_id).first()
                    if account:
                        user = db.query(User).filter(User.UserID == account.UserID).first()
                        if user and user.IsNotificationsEnabled and user.PushToken:
                            from utils.notifications import send_push_notification
                            account_name = account.AccountName or f"Account {account.AccountLoginNumber}"
                            action_ar = "شراء" if action == "BUY" else "بيع"
                            send_push_notification(
                                token=user.PushToken,
                                title=f"صفقة {action_ar} جديدة 🚀",
                                body=f"{action} {user_symbol} @ {result.price}\nالحساب: {account_name}",
                                data={"trade_id": result.order, "account_name": account_name}
                            )
                    db.close()
                except Exception as e:
                    self.logger.error(f"⚠️ Failed to send notification: {e}")
            else:
                self.logger.error("❌ Failed to save trade to DB")

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
        import traceback
        traceback.print_exc()
        return False


"""
Update the AccountMonitor __init__ to store account_id:
"""

def __init___UPDATED(self, account_name, credentials, shared_state, strategy_type, mt5_context, account_id):
    self.account_name = account_name
    self.credentials = credentials
    self.shared_state = shared_state
    self.strategy_type = strategy_type
    self.mt5_context = mt5_context
    self.account_id = account_id  # ✅ Add this
    
    self.script_dir = os.path.dirname(os.path.abspath(__file__))
    self.models_dir = os.path.join(self.script_dir, MODELS_DIR)
    self.scalers_dir = os.path.join(self.script_dir, SCALERS_DIR)
    
    self.used_zones = set()
    
    self._setup_logging()


"""
Update the main() function to fetch accounts from database:
"""

def main_UPDATED():
    """
    Updated main function that fetches accounts from database
    """
    print("\n" + "="*60)
    print("🚀 DUAL ACCOUNT TRADING SYSTEM - DATABASE INTEGRATED")
    print("="*60)
    
    # Import account helper
    from utils.account_helper import get_active_accounts
    
    # Fetch all active accounts from database
    accounts = get_active_accounts()
    
    if not accounts:
        print("❌ No active accounts found in database!")
        print("   Please add accounts via the web interface first.")
        return
    
    print(f"\n✅ Found {len(accounts)} active account(s)")
    
    # Initialize shared state and MT5 context
    shared_state = SharedState()
    mt5_context = MT5Context()
    
    # Fetch daily news
    shared_state.fetch_daily_news()
    
    # Start data updater thread
    data_thread = threading.Thread(
        target=data_updater_thread,
        args=(shared_state,),
        daemon=True
    )
    data_thread.start()
    print("✅ Data Updater Thread Started")
    
    # Create monitors for each account based on their strategy
    monitors = []
    
    for account in accounts:
        account_id = account['account_id']
        strategy = account.get('trading_strategy', 'None')
        
        credentials = {
            'login': account['login'],
            'password': account['password'],
            'server': account['server']
        }
        
        print(f"\n📊 Account: {account_id} | Strategy: {strategy}")
        
        # Create appropriate monitor based on strategy
        if strategy == 'All':  # Advanced
            monitor = AdvancedStrategyMonitor(
                credentials=credentials,
                shared_state=shared_state,
                mt5_context=mt5_context,
                account_id=account_id  # ✅ Pass account_id
            )
            monitors.append(monitor)
        elif strategy == 'FVG + Trend':  # Simple
            monitor = SimpleStrategyMonitor(
                credentials=credentials,
                shared_state=shared_state,
                mt5_context=mt5_context,
                account_id=account_id  # ✅ Pass account_id
            )
            monitors.append(monitor)
        elif strategy == 'Voting':
            monitor = VotingStrategyMonitor(
                credentials=credentials,
                shared_state=shared_state,
                mt5_context=mt5_context,
                account_id=account_id  # ✅ Pass account_id
            )
            monitors.append(monitor)
    
    if not monitors:
        print("❌ No monitors created! Check account strategies.")
        return
    
    # Start monitor threads
    threads = []
    for monitor in monitors:
        thread = threading.Thread(target=monitor.run, daemon=True)
        thread.start()
        threads.append(thread)
        print(f"✅ {monitor.account_name} Monitor Started")
    
    print("\n" + "="*60)
    print("✅ ALL SYSTEMS RUNNING")
    print("="*60)
    print("Press Ctrl+C to stop...\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⚠️ Shutting down...")
        shared_state.stop_all()
        for thread in threads:
            thread.join(timeout=5)
        print("✅ Shutdown complete")


if __name__ == "__main__":
    main_UPDATED()
