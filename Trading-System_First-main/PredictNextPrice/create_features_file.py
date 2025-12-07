import joblib
import os

features = ['open', 'high', 'low', 'close', 'volume', 'ret_1', 'ret_3', 'ret_5', 'ret_10', 'ret_20', 'sma_s', 'sma_m', 'sma_l', 'ema_s', 'ema_m', 'ema_l', 'sma_spread_sm', 'sma_spread_ml', 'ema_spread_sm', 'ema_spread_ml', 'atr14', 'vol_sd', 'bb_z', 'rsi', 'sin_dow', 'cos_dow', 'sin_dom', 'cos_dom']

output_dir = 'saved_model_single_train_Full'
output_path = os.path.join(output_dir, 'XAUUSD_features.joblib')

# Ensure the directory exists
os.makedirs(output_dir, exist_ok=True)

joblib.dump(features, output_path)
print(f'Features file created at: {output_path}')