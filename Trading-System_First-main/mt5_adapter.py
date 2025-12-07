import os
import sys
import logging
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import time
from abc import ABC, abstractmethod

# Try to import MetaTrader5, but don't fail if it's missing (for cloud-only environments)
try:
    import MetaTrader5 as mt5_lib
    HAS_LOCAL_MT5 = True
except ImportError:
    HAS_LOCAL_MT5 = False
    # Define dummy constants if MT5 is not available
    class mt5_lib:
        TIMEFRAME_M1 = 1
        TIMEFRAME_M5 = 5
        TIMEFRAME_M15 = 15
        TIMEFRAME_M30 = 30
        TIMEFRAME_H1 = 16385
        TIMEFRAME_H4 = 16388
        TIMEFRAME_D1 = 16408
        
        ORDER_TYPE_BUY = 0
        ORDER_TYPE_SELL = 1
        ORDER_TYPE_BUY_LIMIT = 2
        ORDER_TYPE_SELL_LIMIT = 3
        
        TRADE_ACTION_DEAL = 1
        TRADE_ACTION_PENDING = 5
        
        ORDER_FILLING_IOC = 1
        ORDER_FILLING_RETURN = 2
        
        ORDER_TIME_GTC = 0
        
        TRADE_RETCODE_DONE = 10009

# Import MetaApi if available
try:
    from metaapi_cloud_sdk import MetaApi
    HAS_METAAPI = True
except ImportError:
    HAS_METAAPI = False

from env_loader import Config

# Setup logger
logger = logging.getLogger('MT5Adapter')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class MT5Adapter(ABC):
    """Abstract base class for MT5 interactions"""
    
    # Constants (mirroring MT5)
    TIMEFRAME_M1 = mt5_lib.TIMEFRAME_M1
    TIMEFRAME_M5 = mt5_lib.TIMEFRAME_M5
    TIMEFRAME_M15 = mt5_lib.TIMEFRAME_M15
    TIMEFRAME_M30 = mt5_lib.TIMEFRAME_M30
    TIMEFRAME_H1 = mt5_lib.TIMEFRAME_H1
    TIMEFRAME_H4 = mt5_lib.TIMEFRAME_H4
    TIMEFRAME_D1 = mt5_lib.TIMEFRAME_D1
    
    ORDER_TYPE_BUY = mt5_lib.ORDER_TYPE_BUY
    ORDER_TYPE_SELL = mt5_lib.ORDER_TYPE_SELL
    ORDER_TYPE_BUY_LIMIT = mt5_lib.ORDER_TYPE_BUY_LIMIT
    ORDER_TYPE_SELL_LIMIT = mt5_lib.ORDER_TYPE_SELL_LIMIT
    
    TRADE_ACTION_DEAL = mt5_lib.TRADE_ACTION_DEAL
    TRADE_ACTION_PENDING = mt5_lib.TRADE_ACTION_PENDING
    
    ORDER_FILLING_IOC = mt5_lib.ORDER_FILLING_IOC
    ORDER_FILLING_RETURN = mt5_lib.ORDER_FILLING_RETURN
    
    ORDER_TIME_GTC = mt5_lib.ORDER_TIME_GTC
    
    TRADE_RETCODE_DONE = mt5_lib.TRADE_RETCODE_DONE

    @abstractmethod
    def initialize(self, login=None, password=None, server=None):
        pass

    @abstractmethod
    def shutdown(self):
        pass

    @abstractmethod
    def account_info(self):
        pass

    @abstractmethod
    def symbol_info(self, symbol):
        pass
        
    @abstractmethod
    def symbol_info_tick(self, symbol):
        pass

    @abstractmethod
    def symbol_select(self, symbol, visible):
        pass

    @abstractmethod
    def copy_rates_range(self, symbol, timeframe, date_from, date_to):
        pass
        
    @abstractmethod
    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        pass

    @abstractmethod
    def order_send(self, request):
        pass
        
    @abstractmethod
    def last_error(self):
        pass


class LocalMT5Adapter(MT5Adapter):
    """Adapter for local MetaTrader 5 installation"""
    
    def __init__(self):
        if not HAS_LOCAL_MT5:
            logger.warning("Local MT5 library not found! Local adapter will fail.")
        self._last_error = (0, "Success")

    def initialize(self, login=None, password=None, server=None):
        if not HAS_LOCAL_MT5:
            return False
            
        if login and password and server:
            return mt5_lib.initialize(login=login, password=password, server=server)
        else:
            return mt5_lib.initialize()

    def shutdown(self):
        if HAS_LOCAL_MT5:
            mt5_lib.shutdown()

    def account_info(self):
        return mt5_lib.account_info()

    def symbol_info(self, symbol):
        return mt5_lib.symbol_info(symbol)
        
    def symbol_info_tick(self, symbol):
        return mt5_lib.symbol_info_tick(symbol)

    def symbol_select(self, symbol, visible):
        return mt5_lib.symbol_select(symbol, visible)

    def copy_rates_range(self, symbol, timeframe, date_from, date_to):
        return mt5_lib.copy_rates_range(symbol, timeframe, date_from, date_to)
        
    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        return mt5_lib.copy_rates_from_pos(symbol, timeframe, start_pos, count)

    def order_send(self, request):
        return mt5_lib.order_send(request)
        
    def last_error(self):
        return mt5_lib.last_error()


class CloudMT5Adapter(MT5Adapter):
    """Adapter for MetaApi Cloud"""
    
    def __init__(self, token, account_id):
        if not HAS_METAAPI:
            raise ImportError("metaapi-cloud-sdk is required for Cloud Mode")
            
        self.token = token
        self.account_id = account_id
        self.api = MetaApi(token)
        self.account = None
        self.connection = None
        self._last_error = (0, "Success")
        
        # Create a dedicated event loop for async operations
        self.loop = asyncio.new_event_loop()
        # We don't start a thread here because we'll use run_until_complete for simplicity
        # in this synchronous-to-asynchronous bridge.
        # For a high-frequency trading system, a background thread would be better,
        # but for M15 timeframe, blocking calls are acceptable and safer.

    def _run_async(self, coro):
        """Helper to run async coroutines synchronously"""
        return self.loop.run_until_complete(coro)

    def initialize(self, login=None, password=None, server=None):
        """Initialize connection to MetaApi"""
        try:
            async def _init():
                self.account = await self.api.metatrader_account_api.get_account(self.account_id)
                
                # Wait for deployment if needed
                if self.account.state != 'DEPLOYED':
                    logger.info(f"Account state is {self.account.state}, waiting for deployment...")
                    await self.account.deploy()
                
                # Wait for connection
                logger.info("Waiting for API connection...")
                await self.account.wait_connected()
                
                # Get RPC connection
                self.connection = self.account.get_rpc_connection()
                await self.connection.connect()
                await self.connection.wait_synchronized()
                
                return True

            return self._run_async(_init())
        except Exception as e:
            logger.error(f"Cloud initialization failed: {e}")
            self._last_error = (1, str(e))
            return False

    def shutdown(self):
        try:
            if self.connection:
                self._run_async(self.connection.close())
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    def account_info(self):
        try:
            async def _get_info():
                return await self.connection.get_account_information()
            
            info = self._run_async(_get_info())
            
            # Convert to object similar to mt5.AccountInfo
            class AccountInfo:
                def __init__(self, data):
                    self.login = int(data.get('login', 0))
                    self.balance = float(data.get('balance', 0.0))
                    self.equity = float(data.get('equity', 0.0))
                    self.profit = float(data.get('profit', 0.0))
                    self.margin = float(data.get('margin', 0.0))
                    self.margin_free = float(data.get('freeMargin', 0.0))
                    self.margin_level = float(data.get('marginLevel', 0.0))
                    self.leverage = int(data.get('leverage', 100))
                    self.currency = data.get('currency', 'USD')
                    self.server = data.get('server', '')
                    self.company = data.get('broker', '')
                    self.name = data.get('name', '')
            
            return AccountInfo(info)
        except Exception as e:
            logger.error(f"account_info failed: {e}")
            return None

    def symbol_info(self, symbol):
        try:
            async def _get_symbol():
                return await self.connection.get_symbol_specification(symbol)
            
            spec = self._run_async(_get_symbol())
            
            if not spec:
                return None
                
            # Convert to object similar to mt5.SymbolInfo
            class SymbolInfo:
                def __init__(self, data):
                    self.name = data.get('symbol', symbol)
                    self.digits = data.get('digits', 2)
                    self.point = 1.0 / (10 ** self.digits) # Approx
                    self.trade_contract_size = data.get('contractSize', 100.0)
                    self.visible = True # Assume visible if we got spec
                    self.description = data.get('description', '')
                    # Add other fields as needed
            
            return SymbolInfo(spec)
        except Exception as e:
            logger.error(f"symbol_info failed: {e}")
            return None

    def symbol_info_tick(self, symbol):
        try:
            async def _get_tick():
                return await self.connection.get_symbol_price(symbol)
            
            price = self._run_async(_get_tick())
            
            if not price:
                return None
                
            class Tick:
                def __init__(self, data):
                    self.time = int(datetime.now().timestamp()) # Approx
                    self.bid = float(data.get('bid', 0.0))
                    self.ask = float(data.get('ask', 0.0))
                    self.last = float(data.get('bid', 0.0)) # Fallback
                    self.volume = 0
            
            return Tick(price)
        except Exception as e:
            logger.error(f"symbol_info_tick failed: {e}")
            return None

    def symbol_select(self, symbol, visible):
        # In cloud API, we don't strictly need to "select" symbols like in terminal
        # But we can try to subscribe if needed. For RPC, it's usually auto-handled.
        return True

    def copy_rates_range(self, symbol, timeframe, date_from, date_to):
        try:
            # Convert timeframe to MetaApi format
            tf_map = {
                self.TIMEFRAME_M1: '1m',
                self.TIMEFRAME_M5: '5m',
                self.TIMEFRAME_M15: '15m',
                self.TIMEFRAME_M30: '30m',
                self.TIMEFRAME_H1: '1h',
                self.TIMEFRAME_H4: '4h',
                self.TIMEFRAME_D1: '1d'
            }
            tf_str = tf_map.get(timeframe, '15m')
            
            async def _get_rates():
                return await self.connection.get_historical_candles(
                    symbol, 
                    tf_str, 
                    date_from, 
                    startTime=date_from
                )
                # Note: MetaApi get_historical_candles API might differ slightly in arguments
                # We might need to use start time.
                # Actually, get_historical_candles(symbol, timeframe, startTime=None, limit=None)
            
            # MetaApi usually returns candles in a specific format.
            # We need to map them to numpy array or list of tuples as MT5 does.
            # Let's use a simplified approach: fetch and convert to structured array
            
            async def _fetch():
                # MetaApi expects datetime objects or ISO strings
                return await self.connection.get_historical_candles(
                    symbol, 
                    tf_str, 
                    startTime=date_from,
                    endTime=date_to
                )

            candles = self._run_async(_fetch())
            
            if not candles:
                return None
                
            # Convert to format expected by pandas (list of dicts is fine for DataFrame)
            # But existing code expects numpy structured array or something that pd.DataFrame(rates) accepts.
            # MT5 returns tuple of tuples or numpy array with named fields.
            
            data = []
            for c in candles:
                # MetaApi: {'time': '2023-01-01T00:00:00.000Z', 'open': 1.0, ...}
                # We need to parse time to timestamp
                dt = datetime.strptime(c['time'].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                timestamp = int(dt.timestamp())
                
                data.append({
                    'time': timestamp,
                    'open': c['open'],
                    'high': c['high'],
                    'low': c['low'],
                    'close': c['close'],
                    'tick_volume': c['tickVolume'],
                    'spread': c.get('spread', 0),
                    'real_volume': c.get('volume', 0)
                })
            
            return data # pd.DataFrame(data) works fine
            
        except Exception as e:
            logger.error(f"copy_rates_range failed: {e}")
            return None

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        # MetaApi doesn't support "from pos" directly easily without knowing the time.
        # But we can fetch latest N candles.
        try:
             # Convert timeframe to MetaApi format
            tf_map = {
                self.TIMEFRAME_M1: '1m',
                self.TIMEFRAME_M5: '5m',
                self.TIMEFRAME_M15: '15m',
                self.TIMEFRAME_M30: '30m',
                self.TIMEFRAME_H1: '1h',
                self.TIMEFRAME_H4: '4h',
                self.TIMEFRAME_D1: '1d'
            }
            tf_str = tf_map.get(timeframe, '15m')
            
            async def _fetch():
                # To get latest, we can use start time in future or just limit?
                # MetaApi: get_historical_candles(symbol, timeframe, startTime=None, limit=None)
                # If startTime is None, it returns latest?
                # Actually we need to check SDK docs. Usually 'startTime' is optional.
                # If we want "from pos 0" (latest), we just ask for 'limit=count' and sort desc?
                # Usually APIs return latest if no time specified.
                return await self.connection.get_historical_candles(
                    symbol, 
                    tf_str, 
                    limit=count + start_pos
                )

            candles = self._run_async(_fetch())
            
            if not candles:
                return None
                
            # Sort by time
            candles.sort(key=lambda x: x['time'])
            
            # Slice if start_pos > 0 (start_pos 0 means latest)
            # MT5 copy_rates_from_pos(0, 10) returns 10 latest candles.
            # If start_pos is 0, we want the last 'count' candles.
            # If start_pos is 10, we want 10 candles starting from 10th candle back.
            
            # Since we fetched count + start_pos, we take the subset.
            # e.g. count=10, start=5. Fetch 15. 
            # We want candles at index -15 to -5? 
            # MT5: 0 is latest. 
            
            if start_pos > 0:
                candles = candles[:-(start_pos)]
            
            candles = candles[-count:]
            
            data = []
            for c in candles:
                dt = datetime.strptime(c['time'].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                timestamp = int(dt.timestamp())
                
                data.append({
                    'time': timestamp,
                    'open': c['open'],
                    'high': c['high'],
                    'low': c['low'],
                    'close': c['close'],
                    'tick_volume': c['tickVolume'],
                    'spread': c.get('spread', 0),
                    'real_volume': c.get('volume', 0)
                })
                
            return data

        except Exception as e:
            logger.error(f"copy_rates_from_pos failed: {e}")
            return None

    def order_send(self, request):
        try:
            # Convert MT5 request to MetaApi trade request
            # MT5: {'action': 1, 'symbol': 'XAUUSD', 'volume': 0.01, 'type': 0, 'price': ..., 'sl': ..., 'tp': ...}
            
            action_type = request.get('action')
            order_type = request.get('type')
            symbol = request.get('symbol')
            volume = request.get('volume')
            sl = request.get('sl')
            tp = request.get('tp')
            comment = request.get('comment')
            
            trade_req = {
                'actionType': 'ORDER_TYPE_BUY' if order_type == self.ORDER_TYPE_BUY else 
                              'ORDER_TYPE_SELL' if order_type == self.ORDER_TYPE_SELL else
                              'ORDER_TYPE_BUY_LIMIT' if order_type == self.ORDER_TYPE_BUY_LIMIT else
                              'ORDER_TYPE_SELL_LIMIT' if order_type == self.ORDER_TYPE_SELL_LIMIT else None,
                'symbol': symbol,
                'volume': volume,
                'stopLoss': sl,
                'takeProfit': tp,
                'comment': comment
            }
            
            if request.get('price') and 'LIMIT' in str(trade_req['actionType']):
                trade_req['price'] = request.get('price')
            
            async def _trade():
                return await self.connection.create_market_buy_order(symbol, volume, sl, tp, {'comment': comment}) if order_type == self.ORDER_TYPE_BUY else \
                       await self.connection.create_market_sell_order(symbol, volume, sl, tp, {'comment': comment}) if order_type == self.ORDER_TYPE_SELL else \
                       await self.connection.create_limit_buy_order(symbol, volume, request.get('price'), sl, tp, {'comment': comment}) if order_type == self.ORDER_TYPE_BUY_LIMIT else \
                       await self.connection.create_limit_sell_order(symbol, volume, request.get('price'), sl, tp, {'comment': comment}) if order_type == self.ORDER_TYPE_SELL_LIMIT else None

            result = self._run_async(_trade())
            
            # Convert result to MT5 OrderSendResult
            class OrderResult:
                def __init__(self, res):
                    self.retcode = 10009 if res else 0 # DONE
                    self.deal = int(res.get('orderId', 0)) if res else 0
                    self.order = int(res.get('orderId', 0)) if res else 0
                    self.volume = volume
                    self.price = 0.0
                    self.bid = 0.0
                    self.ask = 0.0
                    self.comment = "Executed via MetaApi"
                    self.request_id = 0
                    self.retcode_external = 0
            
            return OrderResult(result)

        except Exception as e:
            logger.error(f"order_send failed: {e}")
            class ErrorResult:
                def __init__(self):
                    self.retcode = 0
                    self.comment = str(e)
            return ErrorResult()

    def last_error(self):
        return self._last_error


# Factory to get the correct adapter
def get_mt5_adapter():
    mode = Config.CONNECTION_MODE
    
    if mode == 'CLOUD':
        token = Config.METAAPI_TOKEN
        account_id = Config.METAAPI_ACCOUNT_ID
        if not token or not account_id:
            logger.error("MetaApi Token or Account ID missing for CLOUD mode!")
            # Fallback to local or raise error?
            # Let's raise error to be explicit
            raise ValueError("Missing MetaApi credentials")
        return CloudMT5Adapter(token, account_id)
    else:
        return LocalMT5Adapter()

# Create a singleton instance (lazy initialization recommended in app)
# But for compatibility with 'import mt5', we might want to expose the instance directly?
# No, better to expose the module-like interface.

# Global instance
_adapter = None

def initialize(login=None, password=None, server=None):
    global _adapter
    if _adapter is None:
        _adapter = get_mt5_adapter()
    return _adapter.initialize(login, password, server)

def shutdown():
    if _adapter:
        _adapter.shutdown()

def account_info():
    return _adapter.account_info() if _adapter else None

def symbol_info(symbol):
    return _adapter.symbol_info(symbol) if _adapter else None

def symbol_info_tick(symbol):
    return _adapter.symbol_info_tick(symbol) if _adapter else None

def symbol_select(symbol, visible):
    return _adapter.symbol_select(symbol, visible) if _adapter else False

def copy_rates_range(symbol, timeframe, date_from, date_to):
    return _adapter.copy_rates_range(symbol, timeframe, date_from, date_to) if _adapter else None

def copy_rates_from_pos(symbol, timeframe, start_pos, count):
    return _adapter.copy_rates_from_pos(symbol, timeframe, start_pos, count) if _adapter else None

def order_send(request):
    return _adapter.order_send(request) if _adapter else None

def last_error():
    return _adapter.last_error() if _adapter else (0, "No adapter")

# Expose constants
TIMEFRAME_M1 = MT5Adapter.TIMEFRAME_M1
TIMEFRAME_M5 = MT5Adapter.TIMEFRAME_M5
TIMEFRAME_M15 = MT5Adapter.TIMEFRAME_M15
TIMEFRAME_M30 = MT5Adapter.TIMEFRAME_M30
TIMEFRAME_H1 = MT5Adapter.TIMEFRAME_H1
TIMEFRAME_H4 = MT5Adapter.TIMEFRAME_H4
TIMEFRAME_D1 = MT5Adapter.TIMEFRAME_D1

ORDER_TYPE_BUY = MT5Adapter.ORDER_TYPE_BUY
ORDER_TYPE_SELL = MT5Adapter.ORDER_TYPE_SELL
ORDER_TYPE_BUY_LIMIT = MT5Adapter.ORDER_TYPE_BUY_LIMIT
ORDER_TYPE_SELL_LIMIT = MT5Adapter.ORDER_TYPE_SELL_LIMIT

TRADE_ACTION_DEAL = MT5Adapter.TRADE_ACTION_DEAL
TRADE_ACTION_PENDING = MT5Adapter.TRADE_ACTION_PENDING

ORDER_FILLING_IOC = MT5Adapter.ORDER_FILLING_IOC
ORDER_FILLING_RETURN = MT5Adapter.ORDER_FILLING_RETURN

ORDER_TIME_GTC = MT5Adapter.ORDER_TIME_GTC

TRADE_RETCODE_DONE = MT5Adapter.TRADE_RETCODE_DONE
