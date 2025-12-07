'''
This script identifies Fair Value Gaps (FVGs) on M15 XAU/USD data, 
enriches them with contextual features like ATR and displacement candle analysis,
and evaluates their historical performance.
'''

import pandas as pd
import numpy as np
import os

# --- Configuration ---
M15_FILE = "XAUUSD_Candlestick_15_M_BID_31.10.2022-31.10.2025.csv"
H1_FILE = "XAUUSD_Candlestick_1_Hour_BID_14.10.2010-31.10.2025.csv"
OUTPUT_FILE = "fvg_analysis_XAUUSD_M15_4H.csv"
RETEST_WINDOW = 200  # Number of candles to look for a retest
VOLUME_SPIKE_MULTIPLIER = 2.0 # Volume must be this much higher than rolling average
ATR_PERIOD = 14 # Period for Average True Range calculation

# --- Helper Functions ---

def get_session(dt):
    """Determines the trading session based on UTC hour."""
    hour = dt.hour
    if 0 <= hour < 8:
        return 'Asian'
    elif 8 <= hour < 12:
        return 'London'
    elif 12 <= hour < 17:
        return 'New York'
    elif 17 <= hour < 24:
        return 'London Close'
    return 'N/A'

def analyze_fvg_retest_and_reaction(fvg, future_candles):
    """
    Analyzes the price action after an FVG is formed to find retests and reactions.
    """
    fvg_size = fvg['fvg_size']
    retest_info = {
        'retest': False,
        'retest_time': None,
        'reaction_strength': 0,
        'penetration_points': 0, # Initialize penetration
        'label': 'No Retest' # Default label
    }

    retest_candle_index = -1

    # Find the first retest
    for i, candle in future_candles.iterrows():
        if fvg['FVG_Type'] == 'Bullish' and candle['Low'] <= fvg['fvg_top']:
            retest_info['retest'] = True
            retest_candle_index = i
            retest_info['retest_time'] = candle.name
            retest_info['penetration_points'] = fvg['fvg_top'] - candle['Low']
            break
        elif fvg['FVG_Type'] == 'Bearish' and candle['High'] >= fvg['fvg_bottom']:
            retest_info['retest'] = True
            retest_candle_index = i
            retest_info['retest_time'] = candle.name
            retest_info['penetration_points'] = candle['High'] - fvg['fvg_bottom']
            break

    if not retest_info['retest']:
        return retest_info # No retest found in the window

    # If retested, analyze the reaction from the point of retest
    reaction_candles = future_candles.loc[retest_candle_index:]
    
    if fvg['FVG_Type'] == 'Bullish':
        # Price broke through the FVG
        if reaction_candles.iloc[0]['Close'] < fvg['fvg_bottom']:
             retest_info['label'] = 'Weak'
             retest_info['reaction_strength'] = 0
             return retest_info
        
        max_reaction_high = reaction_candles['High'].max()
        reaction_points = max_reaction_high - reaction_candles.iloc[0]['Low']
        
    elif fvg['FVG_Type'] == 'Bearish':
        # Price broke through the FVG
        if reaction_candles.iloc[0]['Close'] > fvg['fvg_top']:
             retest_info['label'] = 'Weak'
             retest_info['reaction_strength'] = 0
             return retest_info

        min_reaction_low = reaction_candles['Low'].min()
        reaction_points = reaction_candles.iloc[0]['High'] - min_reaction_low

    # Calculate reaction strength relative to FVG size
    if fvg_size > 0:
        reaction_strength = reaction_points / fvg_size
        retest_info['reaction_strength'] = round(reaction_strength, 2)

        # Classify the label based on strength
        if reaction_strength >= 2.0:
            retest_info['label'] = 'Strong'
        elif 0.5 <= reaction_strength < 2.0:
            retest_info['label'] = 'Medium'
        else:
            retest_info['label'] = 'Weak'
            
    return retest_info


# --- Main Script ---
def main():
    print("Starting FVG analysis for XAU/USD...")

    # 1. Load and preprocess data
    print(f"Loading data from {M15_FILE} and {H1_FILE}...")
    try:
        m15_df = pd.read_csv(M15_FILE, parse_dates=['Gmt time'], dayfirst=True)
        # إزالة الأسطر المكررة من بيانات الـ 15 دقيقة، مع الإبقاء على أول ظهور للطابع الزمني المكرر

        h1_df = pd.read_csv(H1_FILE, parse_dates=['Gmt time'], dayfirst=True)
    except FileNotFoundError as e:
        print(f"Error: {e}. Make sure the CSV files are in the same directory as the script.")
        return

    m15_df.set_index('Gmt time', inplace=True)
    h1_df.set_index('Gmt time', inplace=True)
    m15_df.sort_index(inplace=True)
    h1_df.sort_index(inplace=True)

    # 2. Align H1 data to M15 start date
    start_date = m15_df.index.min()
    h1_df = h1_df[h1_df.index >= start_date]
    print(f"Data aligned. M15 starts: {start_date}, H1 now starts: {h1_df.index.min()}")

    # 3. Calculate Indicators and Features
    print("Calculating indicators and features...")
    # H1 Bias
    h1_df['ema50_h1'] = h1_df['Close'].ewm(span=50, adjust=False).mean()
    h1_df['bias_H1'] = np.where(h1_df['Close'] > h1_df['ema50_h1'], 'Bullish', 'Bearish')
    
    # Resample H1 bias to M15 timeframe
    m15_df['bias_H1'] = h1_df['bias_H1'].reindex(m15_df.index, method='ffill')

    # M15 Indicators
    m15_df['ema50'] = m15_df['Close'].ewm(span=50, adjust=False).mean()
    m15_df['ema200'] = m15_df['Close'].ewm(span=200, adjust=False).mean()
    m15_df['ema50_dir'] = np.where(m15_df['Close'] > m15_df['ema50'], 'Above', 'Below')
    m15_df['ema200_dir'] = np.where(m15_df['Close'] > m15_df['ema200'], 'Above', 'Below')
    
    # ATR for volatility context
    high_low = m15_df['High'] - m15_df['Low']
    high_close = np.abs(m15_df['High'] - m15_df['Close'].shift())
    low_close = np.abs(m15_df['Low'] - m15_df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    m15_df['atr'] = true_range.ewm(alpha=1/ATR_PERIOD, adjust=False).mean()

    # Session
    m15_df['session'] = [get_session(dt) for dt in m15_df.index]
    
    # Volume Spike
    m15_df['volume_ma'] = m15_df['Volume'].rolling(window=20).mean()
    m15_df['volume_spike_at_fvg'] = m15_df['Volume'] > (m15_df['volume_ma'] * VOLUME_SPIKE_MULTIPLIER)

    # 4. Identify FVGs
    print("Identifying Fair Value Gaps (FVGs) with enhanced features...")
    fvg_list = []
    # Ensure there's enough data for ATR calculation to be stable
    for i in range(max(1, ATR_PERIOD), len(m15_df) - 1):
        prev_candle = m15_df.iloc[i-1]
        curr_candle = m15_df.iloc[i]
        next_candle = m15_df.iloc[i+1]

        fvg_data = None

        # Bullish FVG: Gap between prev high and next low
        if next_candle['Low'] > prev_candle['High']:
            fvg_data = {
                'FVG_Type': 'Bullish',
                'fvg_bottom': prev_candle['High'],
                'fvg_top': next_candle['Low']
            }

        # Bearish FVG: Gap between prev low and next high
        elif prev_candle['Low'] > next_candle['High']:
            fvg_data = {
                'FVG_Type': 'Bearish',
                'fvg_bottom': next_candle['High'],
                'fvg_top': prev_candle['Low']
            }

        if fvg_data:
            fvg_data['time_created'] = curr_candle.name
            fvg_data['fvg_size'] = fvg_data['fvg_top'] - fvg_data['fvg_bottom']
            fvg_data['fvg_center'] = fvg_data['fvg_bottom'] + fvg_data['fvg_size'] / 2
            
            # --- Add Enhanced Features ---
            # ATR Context
            atr_at_creation = next_candle['atr']
            if atr_at_creation > 0:
                fvg_data['fvg_size_vs_atr'] = fvg_data['fvg_size'] / atr_at_creation
            else:
                fvg_data['fvg_size_vs_atr'] = 0

            # Displacement Candle Analysis (using next_candle)
            creating_candle_body_size = abs(next_candle['Close'] - next_candle['Open'])
            creating_candle_total_range = next_candle['High'] - next_candle['Low']
            fvg_data['creating_candle_body_size'] = creating_candle_body_size
            if creating_candle_total_range > 0:
                fvg_data['creating_candle_body_ratio'] = creating_candle_body_size / creating_candle_total_range
            else:
                fvg_data['creating_candle_body_ratio'] = 0

            # Add original context from the FVG candle
            fvg_data['volume_spike_at_fvg'] = curr_candle['volume_spike_at_fvg']
            fvg_data['session'] = curr_candle['session']
            fvg_data['ema50_dir'] = curr_candle['ema50_dir']
            fvg_data['ema200_dir'] = curr_candle['ema200_dir']
            fvg_data['bias_H1'] = curr_candle['bias_H1']
            
            fvg_list.append(fvg_data)

    if not fvg_list:
        print("No FVGs found.")
        return
        
    print(f"Found {len(fvg_list)} potential FVGs. Now analyzing retests...")

    # 5. Analyze Retests and Reactions
    analyzed_fvgs = []
    total_fvgs = len(fvg_list)
    for i, fvg in enumerate(fvg_list):
        # Get future candles from the point FVG was created
        future_candles_slice = m15_df.loc[fvg['time_created']:].iloc[2:RETEST_WINDOW+2]
        
        if not future_candles_slice.empty:
            retest_analysis = analyze_fvg_retest_and_reaction(fvg, future_candles_slice)
            fvg.update(retest_analysis)
        
        analyzed_fvgs.append(fvg)
        
        if (i + 1) % 1000 == 0:
            print(f"Analyzed {i+1}/{total_fvgs} FVGs...")

    # 6. Create and Save Final DataFrame
    print("Finalizing analysis and saving results...")
    final_df = pd.DataFrame(analyzed_fvgs)
    
    # Reorder columns for clarity
    column_order = [
        'time_created', 'FVG_Type', 'label', 'retest', 'retest_time', 'penetration_points', 'reaction_strength', 
        'fvg_top', 'fvg_bottom', 'fvg_center', 'fvg_size', 'bias_H1', 
        'ema50_dir', 'ema200_dir', 'session', 'volume_spike_at_fvg',
        # New Features
        'fvg_size_vs_atr', 'creating_candle_body_size', 'creating_candle_body_ratio'
    ]
    final_df = final_df.reindex(columns=column_order)

    final_df.to_csv(OUTPUT_FILE, index=False, date_format='%Y-%m-%d %H:%M:%S')
    print(f"Analysis complete. Results saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()