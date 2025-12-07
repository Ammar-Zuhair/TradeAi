
import pandas as pd
import numpy as np
import joblib
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import os

# --- الإعدادات والمتغيرات الأساسية ---
# المسارات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_PATH = os.path.join(BASE_DIR, 'XAUUSD-15M.csv')
MODEL_DIR = os.path.join(BASE_DIR, 'saved_model_single_train_Full')
OUTPUT_DIR = os.path.join(BASE_DIR, 'prediction_comparison_output')

# التأكد من وجود مجلد المخرجات
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- تحميل النموذج والمعالج ---
model = lgb.Booster(model_file=os.path.join(MODEL_DIR, 'XAUUSD_lgbm_model.txt'))
scaler = joblib.load(os.path.join(MODEL_DIR, 'XAUUSD_scaler.joblib'))
feature_names = joblib.load(os.path.join(MODEL_DIR, 'XAUUSD_features.joblib'))

# --- تحميل وهندسة الميزات لبيانات الاختبار ---
df_test = pd.read_csv(TEST_DATA_PATH)
df_test.columns = df_test.columns.str.lower()
df_test.rename(columns={'gmt time': 'date'}, inplace=True)
df_test['date'] = pd.to_datetime(df_test['date'], format='%d.%m.%Y %H:%M:%S.%f')
df_test.set_index('date', inplace=True)

# Feature Engineering (from original script)
periods = [1, 3, 5, 10, 20]
for p in periods:
    df_test[f'ret_{p}'] = df_test['close'].pct_change(p)

sma_s = 5
sma_m = 20
sma_l = 60

df_test['sma_s'] = df_test['close'].rolling(sma_s).mean()
df_test['sma_m'] = df_test['close'].rolling(sma_m).mean()
df_test['sma_l'] = df_test['close'].rolling(sma_l).mean()

df_test['ema_s'] = df_test['close'].ewm(span=sma_s).mean()
df_test['ema_m'] = df_test['close'].ewm(span=sma_m).mean()
df_test['ema_l'] = df_test['close'].ewm(span=sma_l).mean()

df_test['sma_spread_sm'] = df_test['sma_s'] - df_test['sma_m']
df_test['sma_spread_ml'] = df_test['sma_m'] - df_test['sma_l']

df_test['ema_spread_sm'] = df_test['ema_s'] - df_test['ema_m']
df_test['ema_spread_ml'] = df_test['ema_m'] - df_test['ema_l']

# ATR
df_test['tr'] = np.maximum(df_test['high'], df_test['close'].shift()) - np.minimum(df_test['low'], df_test['close'].shift())
df_test['atr14'] = df_test['tr'].rolling(14).mean()

# Volatility
df_test['vol_sd'] = df_test['ret_1'].rolling(20).std()

# Bollinger Bands
df_test['bb_m'] = df_test['close'].rolling(20).mean()
df_test['bb_s'] = df_test['close'].rolling(20).std()
df_test['bb_z'] = (df_test['close'] - df_test['bb_m']) / df_test['bb_s']

# RSI
change = df_test['close'].diff()
gain = change.mask(change < 0, 0)
loss = -change.mask(change > 0, 0)

avg_gain = gain.ewm(com=13, min_periods=14).mean()
avg_loss = loss.ewm(com=13, min_periods=14).mean()

rs = avg_gain / avg_loss
df_test['rsi'] = 100 - (100 / (1 + rs))

# Day of week/month
df_test['sin_dow'] = np.sin(2 * np.pi * df_test.index.dayofweek / 7)
df_test['cos_dow'] = np.cos(2 * np.pi * df_test.index.dayofweek / 7)

df_test['sin_dom'] = np.sin(2 * np.pi * df_test.index.day / 31)
df_test['cos_dom'] = np.cos(2 * np.pi * df_test.index.day / 31)

df_test.dropna(inplace=True)

# تحجيم الميزات
X_test = df_test[feature_names]
X_test_scaled = scaler.transform(X_test)

# --- توليد التنبؤات ---
predicted_log_returns = model.predict(X_test_scaled)
df_test['predicted_log_return'] = predicted_log_returns
df_test['predicted_close'] = df_test['close'] * np.exp(df_test['predicted_log_return'])

# --- حساب مقاييس الدقة ---
mae = mean_absolute_error(df_test['close'], df_test['predicted_close'])
mse = mean_squared_error(df_test['close'], df_test['predicted_close'])
rmse = np.sqrt(mse)

# حساب نسبة التغير المتوقعة مقابل الفعلية
df_test['actual_return'] = df_test['close'].pct_change()
df_test['predicted_return'] = df_test['predicted_close'].pct_change()
df_test['return_diff'] = df_test['predicted_return'] - df_test['actual_return']

# --- حفظ النتائج ---
# إنشاء ملف CSV لمقارنة الأسعار
comparison_df = df_test[['close', 'predicted_close', 'actual_return', 'predicted_return', 'return_diff']].copy()
comparison_csv_path = os.path.join(OUTPUT_DIR, 'price_comparison.csv')
comparison_df.to_csv(comparison_csv_path)
print(f"Price comparison data saved to {comparison_csv_path}")

# --- طباعة مقاييس الدقة ---
print(f"Model Accuracy Metrics:")
print(f"Mean Absolute Error (MAE): {mae:.5f}")
print(f"Mean Squared Error (MSE): {mse:.5f}")
print(f"Root Mean Squared Error (RMSE): {rmse:.5f}")
print(f"Average Prediction Error: {df_test['return_diff'].abs().mean():.5f}")

# --- رسم المخططات ---

# 1. مخطط مقارنة الأسعار الفعلية والمتوقعة
plt.figure(figsize=(15, 8))
plt.plot(df_test.index, df_test['close'], label='Actual Close Price', color='blue', alpha=0.7)
plt.plot(df_test.index, df_test['predicted_close'], label='Predicted Close Price', color='red', alpha=0.7)
plt.title('Actual vs Predicted Close Prices')
plt.xlabel('Date')
plt.ylabel('Price')
plt.legend()
plt.grid(True)
price_comparison_path = os.path.join(OUTPUT_DIR, 'price_comparison.png')
plt.savefig(price_comparison_path)
plt.close()
print(f"Price comparison chart saved to {price_comparison_path}")

# 2. مخطط الخطأ في التنبؤ
plt.figure(figsize=(15, 6))
plt.plot(df_test.index, df_test['return_diff'], label='Prediction Error', color='purple')
plt.axhline(y=0, color='gray', linestyle='--')
plt.title('Prediction Error (Predicted Return - Actual Return)')
plt.xlabel('Date')
plt.ylabel('Error')
plt.legend()
plt.grid(True)
error_plot_path = os.path.join(OUTPUT_DIR, 'prediction_error.png')
plt.savefig(error_plot_path)
plt.close()
print(f"Prediction error chart saved to {error_plot_path}")

# 3. مخطط توزيع الخطأ
plt.figure(figsize=(10, 6))
plt.hist(df_test['return_diff'], bins=50, color='purple', alpha=0.7, edgecolor='black')
plt.title('Distribution of Prediction Errors')
plt.xlabel('Error')
plt.ylabel('Frequency')
plt.grid(True)
error_dist_path = os.path.join(OUTPUT_DIR, 'prediction_error_distribution.png')
plt.savefig(error_dist_path)
plt.close()
print(f"Prediction error distribution chart saved to {error_dist_path}")

# 4. مخطط مقارنة العوائد
plt.figure(figsize=(15, 8))
plt.plot(df_test.index, df_test['actual_return'].cumsum(), label='Cumulative Actual Returns', color='blue', alpha=0.7)
plt.plot(df_test.index, df_test['predicted_return'].cumsum(), label='Cumulative Predicted Returns', color='red', alpha=0.7)
plt.title('Cumulative Actual vs Predicted Returns')
plt.xlabel('Date')
plt.ylabel('Cumulative Return')
plt.legend()
plt.grid(True)
returns_comparison_path = os.path.join(OUTPUT_DIR, 'returns_comparison.png')
plt.savefig(returns_comparison_path)
plt.close()
print(f"Returns comparison chart saved to {returns_comparison_path}")

print("Prediction analysis finished.")
