import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import joblib
import os
from datetime import datetime, timedelta
import warnings
from tensorflow import keras

warnings.filterwarnings('ignore')


class MarketPredictionSystem:
    def __init__(self, symbol='XAUUSD', models_dir='models', scalers_dir='scalers'):
        """
        نظام توقع حركة السوق المتكامل باستخدام MetaTrader 5

        Parameters:
        -----------
        symbol : str
            رمز السهم أو السلعة (مثل: 'XAUUSD', 'EURUSD', 'BTCUSD')
        models_dir : str
            مجلد النماذج المدربة
        scalers_dir : str
            مجلد ملفات التطبيع
        """
        self.symbol = symbol
        self.models_dir = models_dir
        self.scalers_dir = scalers_dir
        self.df = None
        self.mt5_initialized = False

        # تعريف أوزان النماذج (يمكن تعديلها حسب الأداء)
        self.model_weights = {
            'momentum': 0.20,
            'support_resistance': 0.15,
            'trend': 0.20,
            'volatility': 0.10,
            'volume': 0.20,
            'impulse': 0.10,
            'unified': 0.10
        }

    def initialize_mt5(self, login=None, password=None, server=None):
        """
        تهيئة الاتصال بـ MetaTrader 5

        Parameters:
        -----------
        login : int, optional
            رقم الحساب (اختياري - سيستخدم آخر حساب مسجل)
        password : str, optional
            كلمة المرور
        server : str, optional
            اسم السيرفر
        """
        if not mt5.initialize():
            print("❌ فشل تهيئة MetaTrader 5")
            print(f"خطأ: {mt5.last_error()}")
            return False

        print("✅ تم تهيئة MetaTrader 5 بنجاح")

        # تسجيل الدخول إذا تم توفير بيانات الاعتماد
        if login and password and server:
            if not mt5.login(login=login, password=password, server=server):
                print(f"❌ فشل تسجيل الدخول: {mt5.last_error()}")
                return False
            print(f"✅ تم تسجيل الدخول بنجاح للحساب: {login}")

        # عرض معلومات الحساب
        account_info = mt5.account_info()
        if account_info:
            print(f"📊 معلومات الحساب:")
            print(f"   الرصيد: ${account_info.balance:.2f}")
            print(f"   الرافعة المالية: 1:{account_info.leverage}")
            print(f"   الشركة: {account_info.company}")

        self.mt5_initialized = True

        return True

    def fetch_market_data(self, timeframe=mt5.TIMEFRAME_M15, days=1):
        """
        جلب بيانات السوق من MetaTrader 5

        Parameters:
        -----------
        timeframe : int
            الإطار الزمني (mt5.TIMEFRAME_M1, M5, M15, M30, H1, H4, D1, etc.)
        days : int
            عدد الأيام السابقة لجلب البيانات
        """
        if not self.mt5_initialized:
            print("⚠️  يجب تهيئة MT5 أولاً باستخدام initialize_mt5()")
            if not self.initialize_mt5():
                raise ValueError("فشل تهيئة MetaTrader 5")

        print(f"\n{'=' * 60}")
        print(f"جلب بيانات السوق لـ {self.symbol}")
        print(f"{'=' * 60}")

        # التحقق من توفر الرمز
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            available_symbols = [s.name for s in mt5.symbols_get() if 'XAU' in s.name or 'GOLD' in s.name]
            raise ValueError(
                f"❌ الرمز {self.symbol} غير متوفر!\n"
                f"الرموز المتاحة للذهب: {available_symbols[:5]}"
            )

        # تفعيل الرمز إذا لم يكن مفعلاً
        if not symbol_info.visible:
            if not mt5.symbol_select(self.symbol, True):
                raise ValueError(f"فشل تفعيل الرمز {self.symbol}")

        print(f"✅ الرمز متوفر: {symbol_info.description}")

        # حساب التاريخ
        utc_to = datetime.now()
        utc_from = utc_to - timedelta(days=days)

        # جلب البيانات
        rates = mt5.copy_rates_range(self.symbol, timeframe, utc_from, utc_to)

        if rates is None or len(rates) == 0:
            raise ValueError(f"❌ لم يتم جلب أي بيانات للرمز {self.symbol}")

        # تحويل إلى DataFrame
        self.df = pd.DataFrame(rates)

        # تحويل الوقت من Unix timestamp
        self.df['time'] = pd.to_datetime(self.df['time'], unit='s')
        self.df.set_index('time', inplace=True)

        # إعادة تسمية الأعمدة
        self.df.rename(columns={
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'tick_volume': 'volume',
            'real_volume': 'real_volume'
        }, inplace=True)

        # استخدام tick_volume كحجم افتراضي
        if 'volume' not in self.df.columns or self.df['volume'].sum() == 0:
            self.df['volume'] = self.df['tick_volume']

        # حذف الأعمدة غير المطلوبة
        columns_to_keep = ['open', 'high', 'low', 'close', 'volume']
        self.df = self.df[columns_to_keep]

        print(f"✅ تم جلب {len(self.df)} شمعة")
        print(f"📅 من: {self.df.index[0]}")
        print(f"📅 إلى: {self.df.index[-1]}")
        print(f"💰 آخر سعر: {self.df['close'].iloc[-1]:.2f}")
        print(f"{'=' * 60}\n")

        return self.df

    def shutdown_mt5(self):
        """إغلاق الاتصال بـ MetaTrader 5"""
        if self.mt5_initialized:
            mt5.shutdown()
            print("✅ تم إغلاق الاتصال بـ MetaTrader 5")
            self.mt5_initialized = False

    def calculate_momentum_indicators(self):
        """حساب مؤشرات الزخم"""
        df = self.df.copy()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # Stochastic
        low_14 = df['low'].rolling(window=14).min()
        high_14 = df['high'].rolling(window=14).max()
        df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()

        # CCI
        tp = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = tp.rolling(window=20).mean()
        mad = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
        df['cci'] = (tp - sma_tp) / (0.015 * mad)

        # MFI
        tp = (df['high'] + df['low'] + df['close']) / 3
        mf = tp * df['volume']
        mf_pos = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
        mf_neg = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
        df['mfi'] = 100 - (100 / (1 + mf_pos / mf_neg))

        # Williams %R
        df['williams_r'] = -100 * ((high_14 - df['close']) / (high_14 - low_14))

        return df[['volume', 'rsi', 'stoch_k', 'stoch_d', 'cci', 'mfi', 'williams_r']].iloc[-1:].copy()

    def calculate_support_resistance_indicators(self):
        """حساب مؤشرات الدعم والمقاومة"""
        df = self.df.copy()

        # Pivot Points
        df['pivot'] = (df['high'] + df['low'] + df['close']) / 3
        df['r1'] = 2 * df['pivot'] - df['low']
        df['r2'] = df['pivot'] + (df['high'] - df['low'])
        df['r3'] = df['high'] + 2 * (df['pivot'] - df['low'])
        df['s1'] = 2 * df['pivot'] - df['high']
        df['s2'] = df['pivot'] - (df['high'] - df['low'])
        df['s3'] = df['low'] - 2 * (df['high'] - df['pivot'])

        # SMA
        df['sma_20'] = df['close'].rolling(window=20).mean()

        # Donchian Channel
        df['donchian_upper'] = df['high'].rolling(window=20).max()
        df['donchian_lower'] = df['low'].rolling(window=20).min()
        df['donchian_middle'] = (df['donchian_upper'] + df['donchian_lower']) / 2

        return df[['close', 'r1', 'r2', 'r3', 'sma_20', 'donchian_middle', 's1', 's2', 's3', 'volume']].iloc[-1:].copy()

    def calculate_trend_indicators(self):
        """حساب مؤشرات الاتجاه"""
        df = self.df.copy()

        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # ADX and DI
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()

        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.rolling(window=14).mean()
        df['plus_di'] = 100 * (plus_dm.rolling(window=14).mean() / atr)
        df['minus_di'] = 100 * (minus_dm.rolling(window=14).mean() / atr)

        # SMAs
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()

        return df[['close', 'macd_histogram', 'plus_di', 'minus_di', 'macd', 'sma_200', 'sma_50', 'volume']].iloc[
               -1:].copy()

    def calculate_volatility_indicators(self):
        """حساب مؤشرات التقلب"""
        df = self.df.copy()

        # ATR
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = df['bb_upper'] - df['bb_lower']

        # Keltner Channels
        df['kc_middle'] = df['close'].ewm(span=20, adjust=False).mean()
        df['kc_upper'] = df['kc_middle'] + (df['atr'] * 2)
        df['kc_lower'] = df['kc_middle'] - (df['atr'] * 2)

        # BB Squeeze
        df['bb_squeeze'] = ((df['bb_upper'] - df['bb_lower']) < (df['kc_upper'] - df['kc_lower'])).astype(int)

        return df[['close', 'kc_upper', 'atr', 'kc_lower', 'bb_squeeze', 'bb_width', 'bb_middle', 'volume']].iloc[
               -1:].copy()

    def calculate_volume_indicators(self):
        """حساب مؤشرات الحجم"""
        df = self.df.copy()

        # VWAP
        df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()

        # Volume ROC
        df['volume_roc'] = df['volume'].pct_change(periods=14) * 100

        # CMF (Chaikin Money Flow)
        mf_multiplier = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        mf_volume = mf_multiplier * df['volume']
        df['cmf'] = mf_volume.rolling(window=20).sum() / df['volume'].rolling(window=20).sum()

        # A/D Line Change
        df['ad_line'] = (mf_multiplier * df['volume']).cumsum()
        df['ad_line_change'] = df['ad_line'].diff()

        return df[['close', 'vwap', 'volume_roc', 'cmf', 'ad_line_change', 'volume']].iloc[-1:].copy()

    def calculate_impulse_indicators(self):
        """حساب مؤشرات Impulse"""
        df = self.df.copy()

        # Stochastic
        low_14 = df['low'].rolling(window=14).min()
        high_14 = df['high'].rolling(window=14).max()
        df['Stoch_K'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
        df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Moving Averages
        df['MA_Fast_Blue'] = df['close'].ewm(span=12, adjust=False).mean()
        df['MA_Slow_Red'] = df['close'].ewm(span=26, adjust=False).mean()

        # MFI (Money Flow Index)
        tp = (df['high'] + df['low'] + df['close']) / 3
        mf = tp * df['volume']
        mf_pos = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
        mf_neg = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
        df['MFI'] = 100 - (100 / (1 + mf_pos / mf_neg))

        # OBV (On-Balance Volume)
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i - 1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i - 1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        df['OBV'] = obv

        # ATR (Average True Range)
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=14).mean()

        # ADX and Directional Indicators
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()

        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

        atr = tr.rolling(window=14).mean()
        df['Plus_DI'] = 100 * (plus_dm.rolling(window=14).mean() / atr)
        df['Minus_DI'] = 100 * (minus_dm.rolling(window=14).mean() / atr)

        dx = 100 * abs(df['Plus_DI'] - df['Minus_DI']) / (df['Plus_DI'] + df['Minus_DI'])
        df['ADX'] = dx.rolling(window=14).mean()

        # Bollinger Bands
        df['BB_Middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)

        # Trend Slope
        df['Trend_Slope'] = df['close'].rolling(window=5).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])

        return df[['open', 'high', 'low', 'close', 'volume', 'Stoch_K', 'Stoch_D', 'RSI', 'MA_Fast_Blue', 'MA_Slow_Red',
                   'MFI', 'OBV', 'ADX', 'Plus_DI', 'Minus_DI', 'ATR', 'BB_Upper', 'BB_Middle', 'BB_Lower',
                   'Trend_Slope']].iloc[-1:].copy()

    def calculate_unified_indicators(self):
        """حساب جميع المؤشرات الموحدة"""
        df = self.df.copy()

        # RSI, MFI, CCI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        tp = (df['high'] + df['low'] + df['close']) / 3
        mf = tp * df['volume']
        mf_pos = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
        mf_neg = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
        df['mfi'] = 100 - (100 / (1 + mf_pos / mf_neg))

        sma_tp = tp.rolling(window=20).mean()
        mad = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
        df['cci'] = (tp - sma_tp) / (0.015 * mad)

        # SMAs
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()

        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # ADX and DI
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.rolling(window=14).mean()
        df['atr'] = atr
        df['adx'] = 0  # placeholder
        df['plus_di'] = 100 * (plus_dm.rolling(window=14).mean() / atr)
        df['minus_di'] = 100 * (minus_dm.rolling(window=14).mean() / atr)

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = df['bb_upper'] - df['bb_lower']

        # VWAP
        df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()

        # CMF
        mf_multiplier = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        mf_volume = mf_multiplier * df['volume']
        df['cmf'] = mf_volume.rolling(window=20).sum() / df['volume'].rolling(window=20).sum()

        # Volume ROC
        df['volume_roc'] = df['volume'].pct_change(periods=14) * 100

        # Pivot Points
        df['pivot'] = (df['high'] + df['low'] + df['close']) / 3
        df['r1'] = 2 * df['pivot'] - df['low']
        df['s1'] = 2 * df['pivot'] - df['high']

        # Donchian Channel
        df['donchian_upper'] = df['high'].rolling(window=20).max()
        df['donchian_lower'] = df['low'].rolling(window=20).min()
        df['donchian_middle'] = (df['donchian_upper'] + df['donchian_lower']) / 2

        columns = ['open', 'high', 'low', 'close', 'volume', 'rsi', 'mfi', 'cci', 'sma_20', 'sma_50',
                   'sma_200', 'macd', 'macd_histogram', 'adx', 'plus_di', 'minus_di', 'atr',
                   'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'vwap', 'cmf', 'volume_roc',
                   'pivot', 'r1', 's1', 'donchian_upper', 'donchian_lower', 'donchian_middle']

        return df[columns].iloc[-1:].copy()

    def normalize_data(self, data, model_name):
        """تطبيع البيانات باستخدام ملفات التطبيع المحفوظة"""

        normalization_config = {
            'momentum': {
                'minmax_cols': ['rsi', 'stoch_k', 'stoch_d', 'mfi', 'williams_r'],
                'standard_cols': ['volume', 'cci']
            },
            'support_resistance': {
                'minmax_cols': [],
                'standard_cols': ['close', 'r1', 'r2', 'r3', 'sma_20', 'donchian_middle', 's1', 's2', 's3', 'volume']
            },
            'trend': {
                'minmax_cols': [],
                'standard_cols': ['close', 'macd_histogram', 'plus_di', 'minus_di', 'macd', 'sma_200', 'sma_50',
                                  'volume']
            },
            'volatility': {
                'minmax_cols': [],
                'standard_cols': ['close', 'kc_upper', 'atr', 'kc_lower', 'bb_squeeze', 'bb_width', 'bb_middle',
                                  'volume']
            },
            'volume': {
                'minmax_cols': [],
                'standard_cols': ['close', 'vwap', 'volume_roc', 'cmf', 'ad_line_change', 'volume']
            },
            'impulse': {
                'minmax_cols': [],
                'standard_cols': ['open', 'high', 'low', 'close', 'volume',
                                  'Stoch_K', 'Stoch_D', 'RSI',
                                  'MA_Fast_Blue', 'MA_Slow_Red',
                                  'MFI', 'OBV', 'ADX', 'Plus_DI', 'Minus_DI',
                                  'ATR', 'BB_Upper', 'BB_Middle', 'BB_Lower', 'Trend_Slope']
            },
            'unified': {
                'minmax_cols': [],
                'standard_cols': ['open', 'high', 'low', 'close', 'volume', 'rsi', 'mfi', 'cci', 'sma_20',
                                  'sma_50', 'sma_200', 'macd', 'macd_histogram', 'adx', 'plus_di', 'minus_di',
                                  'atr', 'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'vwap', 'cmf',
                                  'volume_roc', 'pivot', 'r1', 's1', 'donchian_upper', 'donchian_lower',
                                  'donchian_middle']
            }
        }

        config = normalization_config[model_name]
        normalized_data = data.copy()

        # تطبيع MinMax
        if config['minmax_cols']:
            scaler_path = os.path.join(self.scalers_dir, f'{model_name}_minmax_scaler.pkl')
            if os.path.exists(scaler_path):
                minmax_scaler = joblib.load(scaler_path)
                existing_cols = [col for col in config['minmax_cols'] if col in normalized_data.columns]
                if existing_cols:
                    normalized_data[existing_cols] = minmax_scaler.transform(normalized_data[existing_cols])
            else:
                print(f"⚠️  ملف التطبيع MinMax غير موجود: {scaler_path}")

        # تطبيع Standard
        if config['standard_cols']:
            scaler_path = os.path.join(self.scalers_dir, f'{model_name}_standard_scaler.pkl')
            if os.path.exists(scaler_path):
                standard_scaler = joblib.load(scaler_path)
                existing_cols = [col for col in config['standard_cols'] if col in normalized_data.columns]
                if existing_cols:
                    normalized_data[existing_cols] = standard_scaler.transform(normalized_data[existing_cols])
            else:
                print(f"⚠️  ملف التطبيع Standard غير موجود: {scaler_path}")

        return normalized_data

    def predict_with_model(self, model_name, data):
        """التنبؤ باستخدام نموذج معين"""
        model_path = os.path.join(self.models_dir, f'Conv1D_Deep_{model_name}.keras')

        if not os.path.exists(model_path):
            print(f"⚠️  النموذج غير موجود: {model_path}")
            return None

        model = keras.models.load_model(model_path)
        prediction = model.predict(data, verbose=0)

        prediction = np.argmax(prediction, axis=1)

        # استخراج احتمالية التنبؤ إذا كانت متاحة
        try:
            proba = model.predict(data, verbose=0)[0]
            confidence = max(proba)
        except:
            confidence = 0.5

        return {
            'prediction': prediction[0],
            'confidence': confidence
        }

    def get_final_recommendation(self):
        """الحصول على التوصية النهائية من جميع النماذج"""
        print("\n" + "=" * 60)
        print("بدء عملية التنبؤ والتصويت")
        print("=" * 60)

        # حساب جميع المؤشرات
        indicators = {}
        indicators['momentum'] = self.calculate_momentum_indicators()
        indicators['support_resistance'] = self.calculate_support_resistance_indicators()
        indicators['trend'] = self.calculate_trend_indicators()
        indicators['volatility'] = self.calculate_volatility_indicators()
        indicators['volume'] = self.calculate_volume_indicators()
        indicators['impulse'] = self.calculate_impulse_indicators()
        indicators['unified'] = self.calculate_unified_indicators()

        # تطبيع البيانات والتنبؤ
        predictions = {}
        votes = {'buy': 0, 'sell': 0, 'hold': 0}

        for model_name, data in indicators.items():
            print(f"\n📊 معالجة نموذج: {model_name}")

            # تطبيع البيانات
            normalized_data = self.normalize_data(data, model_name)

            # التنبؤ
            result = self.predict_with_model(model_name, normalized_data)

            if result:
                predictions[model_name] = result
                prediction = result['prediction']
                confidence = result['confidence']
                weight = self.model_weights[model_name]

                # إضافة الصوت المرجح
                if isinstance(prediction, (int, np.integer)):
                    # تحويل الأرقام إلى توصيات
                    actions = ['sell', 'hold', 'buy']
                    if 0 <= prediction < len(actions):
                        action = actions[prediction]
                    else:
                        action = 'hold'
                else:
                    action = str(prediction).lower()

                weighted_vote = weight * confidence
                votes[action] = votes.get(action, 0) + weighted_vote

                print(f"   التنبؤ: {action}")
                print(f"   الثقة: {confidence:.2%}")
                print(f"   الوزن: {weight}")
                print(f"   الصوت المرجح: {weighted_vote:.4f}")

        # التوصية النهائية
        print("\n" + "=" * 60)
        print("نتائج التصويت المرجح:")
        print("=" * 60)

        for action, vote in votes.items():
            print(f"{action.upper()}: {vote:.4f}")

        final_recommendation = max(votes, key=votes.get)
        final_confidence = votes[final_recommendation] / sum(votes.values()) if sum(votes.values()) > 0 else 0

        print("\n" + "=" * 60)
        print(f"🎯 التوصية النهائية: {final_recommendation.upper()}")
        print(f"📊 مستوى الثقة: {final_confidence:.2%}")
        print("=" * 60)

        return {
            'recommendation': final_recommendation,
            'confidence': final_confidence,
            'votes': votes,
            'individual_predictions': predictions,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


# مثال على الاستخدام
if __name__ == "__main__":
    # تهيئة النظام للذهب
    system = MarketPredictionSystem(
        symbol='XAUUSD',  # رمز الذهب
        models_dir='models',
        scalers_dir='scalers'
    )

    try:
        # تهيئة الاتصال بـ MT5 (سيستخدم آخر حساب تم تسجيل الدخول إليه)
        if not system.initialize_mt5():
            print("❌ فشل تهيئة MetaTrader 5")
            exit(1)

        # أو يمكنك تسجيل الدخول يدوياً:
        # system.initialize_mt5(login=YOUR_LOGIN, password="YOUR_PASSWORD", server="YOUR_SERVER")

        # جلب البيانات لتايم فريم 15 دقيقة
        # لضمان وجود بيانات كافية للمؤشرات (خاصة SMA_200)
        # نحتاج على الأقل 200 شمعة × 15 دقيقة = 3000 دقيقة = 50 ساعة ≈ 3 أيام تداول
        system.fetch_market_data(
            timeframe=mt5.TIMEFRAME_M15,  # 15 دقيقة
            days=7
        )


        result = system.get_final_recommendation()

        # طباعة النتائج التفصيلية
        print("\n" + "=" * 60)
        print("📋 ملخص شامل")
        print("=" * 60)
        print(f"الرمز: {system.symbol}")
        print(f"عدد الشموع: {len(system.df)}")
        print(f"آخر سعر: {system.df['close'].iloc[-1]:.2f}")
        print(f"التوصية: {result['recommendation'].upper()}")
        print(f"الثقة: {result['confidence']:.2%}")
        print(f"الوقت: {result['timestamp']}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ حدث خطأ: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # إغلاق الاتصال بـ MT5
        system.shutdown_mt5()

"""
ملاحظات مهمة:
===============

1. تأكد من تثبيت MetaTrader5:
   pip install MetaTrader5

2. يجب أن يكون MetaTrader 5 مفتوحاً ومسجل دخول

3. التايم فريمات المتاحة:
   - mt5.TIMEFRAME_M1  : دقيقة واحدة
   - mt5.TIMEFRAME_M5  : 5 دقائق
   - mt5.TIMEFRAME_M15 : 15 دقيقة
   - mt5.TIMEFRAME_M30 : 30 دقيقة
   - mt5.TIMEFRAME_H1  : ساعة واحدة
   - mt5.TIMEFRAME_H4  : 4 ساعات
   - mt5.TIMEFRAME_D1  : يومي
   - mt5.TIMEFRAME_W1  : أسبوعي
   - mt5.TIMEFRAME_MN1 : شهري

4. رموز الذهب المحتملة:
   - XAUUSD (الأكثر شيوعاً)
   - GOLD
   - تحقق من الرموز المتاحة في الوسيط الخاص بك

5. للحصول على معلومات الحساب:
   account_info = mt5.account_info()
   print(account_info)

6. لعرض جميع الرموز المتاحة:
   symbols = mt5.symbols_get()
   for s in symbols:
       print(s.name)
"""