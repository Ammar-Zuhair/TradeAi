
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib

def run_precise_backtest_dynamic_stop_ml():
    # --- Configuration ---
    INITIAL_CAPITAL = 100.0
    SPREAD_POINTS = 0.5
    RISK_REWARD_RATIO = 8.0
    POINT_VALUE = 1.0
    VOLUME_MA_PERIOD = 20
    SAFE_MARGIN = 0.5  # Safe margin for SL to avoid immediate trigger

    # --- Load Data ---
    try:
        fvg_data = pd.read_csv('fvg_test_data_unlabeled.csv')
        h1_candles = pd.read_csv('XAUUSD_Candlestick_1_Hour_BID.csv')
        m15_candles = pd.read_csv('XAUUSD_Candlestick_15_M_BID_Test.csv')
        model = joblib.load('fvg_strong_classifier.joblib')
    except FileNotFoundError as e:
        print(f"Error loading data: {e}")
        return

    # --- Prepare Data ---
    print("Preparing data...")
    fvg_data['time_created'] = pd.to_datetime(fvg_data['time_created'])
    h1_candles['Gmt time'] = pd.to_datetime(h1_candles['Gmt time'], format='%d.%m.%Y %H:%M:%S.%f')
    m15_candles['Gmt time'] = pd.to_datetime(m15_candles['Gmt time'], format='%d.%m.%Y %H:%M:%S.%f')

    h1_candles.set_index('Gmt time', inplace=True)
    m15_candles.set_index('Gmt time', inplace=True)

    h1_candles['sma50'] = h1_candles['Close'].rolling(window=50).mean()
    h1_candles['h1_trend'] = np.where(h1_candles['Close'] > h1_candles['sma50'], 'Up', 'Down')

    m15_candles['sma50'] = m15_candles['Close'].rolling(window=50).mean()
    m15_candles['m15_trend'] = np.where(m15_candles['Close'] > m15_candles['sma50'], 'Up', 'Down')
    m15_candles['volume_ma'] = m15_candles['Volume'].rolling(window=VOLUME_MA_PERIOD).mean()

    h1_candles.dropna(inplace=True)
    m15_candles.dropna(inplace=True)

    # --- Feature Engineering for Prediction (from directional_backtest.py) ---
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


    # --- Merge Data ---
    print("Merging data...")
    fvg_data['h1_time'] = fvg_data['time_created'].dt.floor('H')
    merged = pd.merge(fvg_data, h1_candles[['h1_trend']], left_on='h1_time', right_index=True, how='left')
    merged = pd.merge(merged, m15_candles[['m15_trend', 'Volume', 'volume_ma']], left_on='time_created', right_index=True, how='left')
    merged.dropna(subset=['h1_trend','m15_trend','Volume','volume_ma', 'recommendation'], inplace=True)
    merged['volume_spike'] = merged['Volume'] > merged['volume_ma']

    # --- Backtest ---
    print("Starting backtest...")
    account_balance = INITIAL_CAPITAL
    trades = []

    for idx, row in merged.iterrows():
        # --- ML Model Filter ---
        is_high_priority = row['recommendation'] in ['High', 'Medium']
        if not is_high_priority:
            continue

        # --- Original Strategy Filters ---
        strategy1 = row['fvg_size'] > 2.5
        strategy2 = (row['session'] == 'New York') and row['volume_spike']
        if not (strategy1 or strategy2):
            continue

        direction = None
        if row['FVG_Type']=='Bullish' and row['h1_trend']=='Up' and row['m15_trend']=='Up':
            direction = 'Buy'
        elif row['FVG_Type']=='Bearish' and row['h1_trend']=='Down' and row['m15_trend']=='Down':
            direction = 'Sell'
        
        if not direction:
            continue

        entry_time = row['time_created']

        # --- Dynamic Stop Loss based on FVG ---
        if direction=='Buy':
            entry_price = row['fvg_bottom'] + SPREAD_POINTS   # Entry at the start of the FVG
            stop_loss = row['fvg_bottom'] - SAFE_MARGIN   # SL dynamically below the zone
        else:  # Sell
            entry_price = row['fvg_top'] - SPREAD_POINTS
            stop_loss = row['fvg_top'] + SAFE_MARGIN     # SL dynamically above the zone

        risk = abs(entry_price - stop_loss)
        if risk <= 0: continue
        
        take_profit = entry_price + risk * RISK_REWARD_RATIO if direction == 'Buy' else entry_price - risk * RISK_REWARD_RATIO

        # --- Simulate trade precisely inside M15 candles ---
        future = m15_candles[m15_candles.index > entry_time]
        pnl, status, exit_time = 0, 'Ongoing', None

        for t, c in future.iterrows():
            candle_low = c['Low']
            candle_high = c['High']
            if direction == 'Buy':
                if candle_low <= stop_loss:
                    pnl = -risk * POINT_VALUE
                    status = 'Loss'
                    exit_time = t
                    break
                elif candle_high >= take_profit:
                    pnl = risk * RISK_REWARD_RATIO * POINT_VALUE
                    status = 'Win'
                    exit_time = t
                    break
            else: # Sell
                if candle_high >= stop_loss:
                    pnl = -risk * POINT_VALUE
                    status = 'Loss'
                    exit_time = t
                    break
                elif candle_low <= take_profit:
                    pnl = risk * RISK_REWARD_RATIO * POINT_VALUE
                    status = 'Win'
                    exit_time = t
                    break

        if exit_time:
            account_balance += pnl
            trades.append({
                'entry_time': entry_time, 'exit_time': exit_time, 'direction': direction,
                'entry_price': entry_price, 'stop_loss': stop_loss, 'take_profit': take_profit,
                'pnl': pnl, 'status': status, 'balance': account_balance,
                'recommendation': row['recommendation'], 'score': row['score']
            })

    # --- Reporting ---
    print("\n--- Backtest Results ---")
    if not trades:
        print("No trades were executed based on the criteria.")
        return

    trades_df = pd.DataFrame(trades)
    wins = trades_df[trades_df['status'] == 'Win']
    losses = trades_df[trades_df['status'] == 'Loss']
    total_trades = len(trades_df)
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0

    print(f"Initial Capital: ${INITIAL_CAPITAL:.2f}")
    print(f"Final Balance: ${account_balance:.2f}")
    print(f"Total P/L: ${account_balance - INITIAL_CAPITAL:.2f}")
    print(f"Total Trades: {total_trades} | Wins: {len(wins)} | Losses: {len(losses)}")
    print(f"Win Rate: {win_rate:.2f}%")

    output_filename = 'precise_dynamic_stop_trades_ml.csv'
    trades_df.to_csv(output_filename, index=False)
    print(f"Trades saved to {output_filename}")

    # --- Charts ---
    plt.figure(figsize=(10, 5))
    plt.plot(trades_df['exit_time'], trades_df['balance'], label='Equity Curve')
    plt.title('Equity Curve (ML Enhanced)')
    plt.xlabel('Time')
    plt.ylabel('Balance ($)')
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.savefig('equity_curve_ml.png')

    plt.figure(figsize=(8, 5))
    plt.hist(trades_df['pnl'], bins=40, color='skyblue', edgecolor='black')
    plt.title('Profit Distribution (ML Enhanced)')
    plt.xlabel('Profit per Trade ($)')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig('profit_distribution_ml.png')

    plt.figure(figsize=(10, 5))
    plt.scatter(trades_df['exit_time'], trades_df['pnl'], c=np.where(trades_df['pnl'] > 0, 'green', 'red'), s=10)
    plt.title('Trade Results Over Time (ML Enhanced)')
    plt.xlabel('Exit Time')
    plt.ylabel('PnL')
    plt.tight_layout()
    plt.savefig('trade_results_over_time_ml.png')

    print("Charts saved.")

if __name__ == '__main__':
    run_precise_backtest_dynamic_stop_ml()
