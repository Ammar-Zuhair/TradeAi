'''
This script performs a directional backtest of an FVG trading strategy.

Strategy Rules:
- Trades are only taken in the direction of the trend on both H1 and M15 timeframes.
- Entry is based on the recommendation from the 'fvg_strong_classifier.joblib' model.
- Entry Price: Start of the FVG zone.
- Stop Loss: 3 points from the other side of the FVG.
- Take Profit: 1:2 Risk/Reward ratio.
- Initial Capital: $100
- Spread: 0.5 points
'''

import pandas as pd
import numpy as np
import joblib
from datetime import timedelta

def run_backtest():
    # --- Configuration ---
    INITIAL_CAPITAL = 100.0
    SPREAD_POINTS = 0.5
    STOP_LOSS_POINTS = 3.0
    RISK_REWARD_RATIO = 2.0
    LOT_SIZE = 0.01
    POINT_VALUE = 1.0 # Assuming 1 point = $1 for 0.01 lot

    # --- Load Data ---
    print("Loading data...")
    try:
        fvg_data = pd.read_csv('fvg_analysis_XAUUSD_M15_4H.csv')
        h1_candles = pd.read_csv('XAUUSD_Candlestick_1_Hour_BID_14.10.2010-31.10.2025.csv')
        m15_candles = pd.read_csv('XAUUSD_Candlestick_15_M_BID_Test.csv')
        model = joblib.load('fvg_strong_classifier.joblib')
    except FileNotFoundError as e:
        print(f"Error loading data: {e}. Make sure all required files are in the directory.")
        return

    # --- Prepare Data ---
    print("Preparing data and calculating trends...")

    # Convert time columns to datetime
    fvg_data['time_created'] = pd.to_datetime(fvg_data['time_created'])
    h1_candles['Gmt time'] = pd.to_datetime(h1_candles['Gmt time'], format='%d.%m.%Y %H:%M:%S.%f')
    m15_candles['Gmt time'] = pd.to_datetime(m15_candles['Gmt time'], format='%d.%m.%Y %H:%M:%S.%f')

    # Set index for candle data
    h1_candles.set_index('Gmt time', inplace=True)
    m15_candles.set_index('Gmt time', inplace=True)

    # Calculate H1 Trend
    h1_candles['sma50'] = h1_candles['Close'].rolling(window=50).mean()
    h1_candles.dropna(inplace=True)
    h1_candles['h1_trend'] = np.where(h1_candles['Close'] > h1_candles['sma50'], 'Up', 'Down')

    # Calculate M15 Trend
    m15_candles['sma50'] = m15_candles['Close'].rolling(window=50).mean()
    m15_candles.dropna(inplace=True)
    m15_candles['m15_trend'] = np.where(m15_candles['Close'] > m15_candles['sma50'], 'Up', 'Down')

    # --- Feature Engineering for Prediction (from predict_on_unlabeled_data.py) ---
    print("Running model predictions...")
    fvg_for_pred = fvg_data.copy()
    quantiles = fvg_for_pred['fvg_size'].quantile([0.33, 0.66]).tolist()
    fvg_for_pred['fvg_size_category'] = pd.cut(fvg_for_pred['fvg_size'], bins=[-np.inf] + quantiles + [np.inf], labels=['Small', 'Medium', 'Large'])
    categorical_features = ['FVG_Type', 'session', 'bias_H1', 'ema50_dir', 'ema200_dir', 'fvg_size_category']
    fvg_for_pred = pd.get_dummies(fvg_for_pred, columns=categorical_features, drop_first=True)
    model_features = model.booster_.feature_name()
    fvg_aligned = fvg_for_pred.reindex(columns=model_features, fill_value=0)
    
    probabilities = model.predict_proba(fvg_aligned)[:, 1]
    fvg_data['score'] = (probabilities * 100).astype(int)
    conditions = [
        (fvg_data['score'] >= 85),
        (fvg_data['score'] >= 60),
        (fvg_data['score'] < 60)
    ]
    choices = ['High', 'Medium', 'Low']
    fvg_data['recommendation'] = np.select(conditions, choices, default='Low')

    # --- Merge Trend Data with FVG Data ---
    fvg_data['h1_time'] = fvg_data['time_created'].dt.floor('H')
    merged_data = pd.merge(fvg_data, h1_candles[['h1_trend']], left_on='h1_time', right_index=True, how='left')
    merged_data = pd.merge(merged_data, m15_candles[['m15_trend']], left_on='time_created', right_index=True, how='left')
    merged_data.dropna(subset=['h1_trend', 'm15_trend'], inplace=True)

    # --- Backtesting Loop ---
    print("Starting backtest...")
    account_balance = INITIAL_CAPITAL
    trades = []
    active_trade = None

    for index, row in merged_data.iterrows():
        # Skip if we are still in an active trade
        if active_trade and row['time_created'] < active_trade['exit_time']:
            continue
        
        trade_direction = None
        is_high_priority = row['recommendation'] in ['High', 'Medium']

        # Determine trade direction based on FVG type and trend alignment
        if row['FVG_Type'] == 'Bullish' and row['h1_trend'] == 'Up' and row['m15_trend'] == 'Up' and is_high_priority:
            trade_direction = 'Buy'
        elif row['FVG_Type'] == 'Bearish' and row['h1_trend'] == 'Down' and row['m15_trend'] == 'Down' and is_high_priority:
            trade_direction = 'Sell'

        if trade_direction:
            entry_time = row['time_created']
            
            if trade_direction == 'Buy':
                entry_price = row['fvg_bottom'] + SPREAD_POINTS
                stop_loss = row['fvg_bottom'] - STOP_LOSS_POINTS
                risk_per_trade = entry_price - stop_loss
                take_profit = entry_price + (risk_per_trade * RISK_REWARD_RATIO)
            else: # Sell
                entry_price = row['fvg_top'] - SPREAD_POINTS
                stop_loss = row['fvg_top'] + STOP_LOSS_POINTS
                risk_per_trade = stop_loss - entry_price
                take_profit = entry_price - (risk_per_trade * RISK_REWARD_RATIO)

            # Find future candles to determine trade outcome
            future_candles = m15_candles[m15_candles.index > entry_time]
            
            exit_time = None
            pnl = 0
            status = 'Ongoing'

            for candle_time, candle in future_candles.iterrows():
                if trade_direction == 'Buy':
                    if candle['Low'] <= stop_loss:
                        status = 'Loss'
                        pnl = -risk_per_trade * POINT_VALUE
                        exit_time = candle_time
                        break
                    elif candle['High'] >= take_profit:
                        status = 'Win'
                        pnl = (risk_per_trade * RISK_REWARD_RATIO) * POINT_VALUE
                        exit_time = candle_time
                        break
                else: # Sell
                    if candle['High'] >= stop_loss:
                        status = 'Loss'
                        pnl = -risk_per_trade * POINT_VALUE
                        exit_time = candle_time
                        break
                    elif candle['Low'] <= take_profit:
                        status = 'Win'
                        pnl = (risk_per_trade * RISK_REWARD_RATIO) * POINT_VALUE
                        exit_time = candle_time
                        break
            
            if exit_time:
                account_balance += pnl
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': exit_time,
                    'direction': trade_direction,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'status': status,
                    'pnl': pnl,
                    'balance': account_balance
                })
                active_trade = trades[-1] # Set the last trade as active to prevent overlap

    # --- Reporting ---
    print("\n--- Backtest Results ---")
    if not trades:
        print("No trades were executed.")
        return

    trades_df = pd.DataFrame(trades)
    wins = trades_df[trades_df['status'] == 'Win']
    losses = trades_df[trades_df['status'] == 'Loss']
    
    total_trades = len(trades_df)
    win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
    total_pnl = trades_df['pnl'].sum()
    
    print(f"Initial Capital: ${INITIAL_CAPITAL:.2f}")
    print(f"Final Balance: ${account_balance:.2f}")
    print(f"Total P/L: ${total_pnl:.2f}")
    print(f"Total Trades: {total_trades}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Number of Wins: {len(wins)}")
    print(f"Number of Losses: {len(losses)}")

    # Save trades to CSV for detailed analysis
    trades_df.to_csv('directional_backtest_trades.csv', index=False)
    print("\nDetailed trade log saved to directional_backtest_trades.csv")

if __name__ == '__main__':
    run_backtest()