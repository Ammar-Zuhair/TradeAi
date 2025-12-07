import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import os
import joblib

# =========================
# إعدادات
# =========================
PAIR = 'XAUUSD'
CSV_PATH = 'XAUUSD-15M.csv'
DATE_COL = 'date'
COLS_MAP = {'Open':'open','High':'high','Low':'low','Close':'close','Volume':'volume'}
SEED = 42
np.random.seed(SEED)

# =========================
# 1) قراءة CSV وتنظيفه
# =========================
def load_dukascopy_daily(csv_path):
    df = pd.read_csv(csv_path)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], format='%d.%m.%Y %H:%M:%S.%f', utc=True)
    df = df.rename(columns=COLS_MAP).set_index(DATE_COL).sort_index()
    df = df[['open','high','low','close','volume']].dropna()
    df = df[(df['high'] >= df['low']) & (df['open'] > 0) & (df['close'] > 0)]
    return df

df = load_dukascopy_daily(CSV_PATH)

# =========================
# 2) هندسة ميزات يومية
# =========================
def add_daily_features(df, win_s=5, win_m=20, win_l=60, vol_win=30):
    x = df.copy()
    c = x['close']

    # عوائد لوغاريتمية
    x['ret_1'] = np.log(c).diff(1)
    for k in [3,5,10,20]:
        x[f'ret_{k}'] = np.log(c).diff(k)

    # متوسطات متحركة/أسية وفروق نسبية
    x['sma_s'] = c.rolling(win_s).mean()
    x['sma_m'] = c.rolling(win_m).mean()
    x['sma_l'] = c.rolling(win_l).mean()
    x['ema_s'] = c.ewm(span=win_s, adjust=False).mean()
    x['ema_m'] = c.ewm(span=win_m, adjust=False).mean()
    x['ema_l'] = c.ewm(span=win_l, adjust=False).mean()
    x['sma_spread_sm'] = (x['sma_s'] - x['sma_m']) / c
    x['sma_spread_ml'] = (x['sma_m'] - x['sma_l']) / c
    x['ema_spread_sm'] = (x['ema_s'] - x['ema_m']) / c
    x['ema_spread_ml'] = (x['ema_m'] - x['ema_l']) / c

    # تذبذب
    tr = np.maximum(x['high']-x['low'],
                    np.maximum((x['high']-c.shift(1)).abs(), (x['low']-c.shift(1)).abs()))
    x['atr14'] = tr.rolling(14).mean() / c
    x['vol_sd'] = x['ret_1'].rolling(vol_win).std()

    # بولنجر و RSI
    ma = c.rolling(win_m).mean()
    sd = c.rolling(win_m).std()
    x['bb_z'] = (c - ma) / (sd + 1e-12)

    delta = c.diff()
    up = delta.clip(lower=0).rolling(14).mean()
    down = (-delta.clip(upper=0)).rolling(14).mean()
    rs = up / (down + 1e-12)
    x['rsi'] = 100 - (100 / (1 + rs))

    # ترميز أسبوعي/شهري بسيط
    dow = x.index.dayofweek
    x['sin_dow'] = np.sin(2*np.pi*dow/7)
    x['cos_dow'] = np.cos(2*np.pi*dow/7)
    dom = x.index.day
    x['sin_dom'] = np.sin(2*np.pi*dom/31)
    x['cos_dom'] = np.cos(2*np.pi*dom/31)

    # الهدف: عائد اليوم التالي
    x['target_r1'] = np.log(c.shift(-1)) - np.log(c)

    x = x.dropna()
    return x

df_feat = add_daily_features(df)

# =========================
# 3) تدريب النموذج دفعة واحدة
# =========================
features = [col for col in df_feat.columns if col not in ['target_r1']]
X = df_feat[features]
y = df_feat['target_r1']

# تهيئة Scaler وتطبيقه
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# إعدادات LightGBM
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
    seed=SEED
)

# تدريب النموذج
train_ds = lgb.Dataset(X_scaled, label=y, feature_name=list(X.columns))
model = lgb.train(lgb_params, train_ds, num_boost_round=1200)

# =========================
# 4) التقييم على بيانات التدريب
# =========================
# ملاحظة: هذا التقييم يقيس أداء النموذج على نفس البيانات التي تدرب عليها،
# وهو لا يعكس الأداء الحقيقي على بيانات جديدة.
r1_hat = model.predict(X_scaled)
c_t = df_feat['close']
c_next_hat = c_t * np.exp(r1_hat)

# إزالة آخر قيمة لأنها لا تملك قيمة حقيقية للمقارنة
c_next_hat = c_next_hat[:-1]
true_next_close = df_feat['close'].shift(-1).dropna()

# التأكد من تطابق الفهارس
c_next_hat = c_next_hat[true_next_close.index]


def rmse(a, b):
    # تأكد من تحويل الأنواع إلى numpy arrays إذا كانت tensors
    a = np.array(a)
    b = np.array(b)
    return np.sqrt(mean_squared_error(a, b))


overall_mae = mean_absolute_error(true_next_close, c_next_hat)
overall_rmse = rmse(true_next_close, c_next_hat)
print(f'{PAIR} Daily Next-Close Prediction (Single Train) -> MAE: {overall_mae:.6f}, RMSE: {overall_rmse:.6f}')

# =========================
# 5) حفظ النموذج وكائن Scaler
# =========================
model_output_dir = 'saved_model_single_train_Full'
if not os.path.exists(model_output_dir):
    os.makedirs(model_output_dir)

# حفظ النموذج
model_path = os.path.join(model_output_dir, f'{PAIR}_lgbm_model.txt')
model.save_model(model_path)
print(f'تم حفظ النموذج في: {model_path}')

# حفظ Scaler
scaler_path = os.path.join(model_output_dir, f'{PAIR}_scaler.joblib')
joblib.dump(scaler, scaler_path)
print(f'تم حفظ Scaler في: {scaler_path}')

# =========================
# 6) الرسوم البيانية
# =========================
output_dir = 'horizon_charts_single_train_Full'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

plt.style.use('seaborn-v0_8')

# إنشاء DataFrame للنتائج
results_df = pd.DataFrame({
    'true_close_next': true_next_close,
    'pred_close_next': c_next_hat
})

# 6.1 مقارنة زمنية
fig, ax = plt.subplots(figsize=(15, 7))
ax.plot(results_df.index, results_df['true_close_next'], label='الإغلاق الفعلي (اليوم التالي)', color='black', linewidth=1.2)
ax.plot(results_df.index, results_df['pred_close_next'], label='الإغلاق المتوقع (اليوم التالي)', color='tab:blue', alpha=0.9)
ax.set_title(f'{PAIR} - مقارنة الإغلاق المتوقع مقابل الفعلي (تدريب دفعة واحدة)')
ax.legend(loc='best'); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'time_series_comparison.png'))
plt.close(fig)

# 6.2 مبعثر المتوقع مقابل الفعلي
fig, ax = plt.subplots(figsize=(6,6))
ax.scatter(results_df['true_close_next'], results_df['pred_close_next'], s=12, alpha=0.5)
lims = [
    min(results_df['true_close_next'].min(), results_df['pred_close_next'].min()),
    max(results_df['true_close_next'].max(), results_df['pred_close_next'].max())
]
ax.plot(lims, lims, 'r--', linewidth=1, label='y = x')
ax.set_xlabel('الإغلاق الفعلي (اليوم التالي)')
ax.set_ylabel('الإغلاق المتوقع (اليوم التالي)')
ax.set_title(f'{PAIR} - Scatter Pred vs True (Single Train)')
ax.legend(); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'scatter_pred_vs_true.png'))
plt.close(fig)

print(f'تم حفظ الرسوم البيانية في مجلد: {output_dir}')
