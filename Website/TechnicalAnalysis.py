import pandas as pd
import sqlite3
import ta
from datetime import datetime


# Define technical indicators
def calculate_indicators(data):
    """
    Calculates technical indicators for the given data.
    Returns the data with indicators and signals.
    """
    print("  Calculating technical indicators...")

    print("    - Computing Moving Averages")
    data['SMA_20'] = data['Last Trade Price'].rolling(window=20).mean()
    data['SMA_50'] = data['Last Trade Price'].rolling(window=50).mean()
    data['EMA_20'] = data['Last Trade Price'].ewm(span=20).mean()
    data['EMA_50'] = data['Last Trade Price'].ewm(span=50).mean()

    print("    - Computing Oscillators")
    data['RSI'] = ta.momentum.RSIIndicator(close=data['Last Trade Price']).rsi()
    data['MACD'] = ta.trend.MACD(close=data['Last Trade Price']).macd()
    data['Stoch'] = ta.momentum.StochasticOscillator(
        high=data['Max'], low=data['Min'], close=data['Last Trade Price']
    ).stoch()
    data['CCI'] = ta.trend.CCIIndicator(
        high=data['Max'], low=data['Min'], close=data['Last Trade Price']
    ).cci()
    data['Williams %R'] = ta.momentum.WilliamsRIndicator(
        high=data['Max'], low=data['Min'], close=data['Last Trade Price']
    ).williams_r()

    print("    - Generating trading signals")
    data['Signal'] = 'Hold'
    data.loc[data['RSI'] < 30, 'Signal'] = 'Buy'
    data.loc[data['RSI'] > 70, 'Signal'] = 'Sell'
    data.loc[data['Last Trade Price'] > data['SMA_20'], 'Signal'] = 'Buy'
    data.loc[data['Last Trade Price'] < data['SMA_20'], 'Signal'] = 'Sell'

    return data


def analyze_for_time_period(data, period):
    """
    Resamples the data for the given time period and calculates indicators.
    Returns the analyzed data with the time period added.
    """
    print(f"  Processing {period} data...")

    if period == 'daily':
        resampled_data = data
    elif period == 'weekly':
        print("    - Resampling to weekly data")
        resampled_data = data.set_index('Date').resample('W').agg({
            'Last Trade Price': 'mean',
            'Max': 'max',
            'Min': 'min',
            'Volume': 'sum'
        }).reset_index()
    elif period == 'monthly':
        print("    - Resampling to monthly data")
        resampled_data = data.set_index('Date').resample('ME').agg({
            'Last Trade Price': 'mean',
            'Max': 'max',
            'Min': 'min',
            'Volume': 'sum'
        }).reset_index()
    else:
        raise ValueError("Invalid period. Must be 'daily', 'weekly', or 'monthly'.")

    analyzed_data = calculate_indicators(resampled_data)
    analyzed_data['time_period'] = period
    return analyzed_data


def technical_analysis(database_path):
    """
    Performs technical analysis on stock data stored in the SQLite database.
    Calculates indicators for three time periods: daily, weekly, and monthly.
    Saves the results in a single table called 'technical_indicators'.
    """
    start_time = datetime.now()
    print(f"\nStarting technical analysis at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    print("\nConnecting to database...")
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    print("Fetching stock data...")
    query = '''
    SELECT 
        issuer_code, 
        "Date", 
        "Last Trade Price", 
        "Max", 
        "Min", 
        "Volume", 
        "Turnover in BEST (denars)" 
    FROM stock_data
    '''
    stock_data = pd.read_sql_query(query, conn)

    print("Processing data...")
    stock_data['Date'] = pd.to_datetime(stock_data['Date'])
    stock_data = stock_data.sort_values(by=['issuer_code', 'Date'])

    issuers = stock_data['issuer_code'].unique()
    periods = ['daily', 'weekly', 'monthly']
    total_combinations = len(issuers) * len(periods)
    current_combination = 0

    print(f"\nAnalyzing {len(issuers)} issuers for {len(periods)} time periods...")
    results = []
    for issuer in issuers:
        print(f"\nProcessing issuer: {issuer}")
        issuer_data = stock_data[stock_data['issuer_code'] == issuer].copy()

        for period in periods:
            current_combination += 1
            print(
                f"\nProgress: {current_combination}/{total_combinations} ({(current_combination / total_combinations) * 100:.1f}%)")

            analyzed_data = analyze_for_time_period(issuer_data, period)
            analyzed_data['issuer_code'] = issuer
            results.append(analyzed_data)

    print("\nCombining results...")
    results_df = pd.concat(results, ignore_index=True)

    print("\nSaving results to database...")
    results_df[['issuer_code', 'Date', 'time_period', 'Signal', 'SMA_20', 'SMA_50', 'EMA_20', 'EMA_50',
                'RSI', 'MACD', 'Stoch', 'CCI', 'Williams %R']].to_sql(
        'technical_indicators', conn, if_exists='replace', index=False
    )

    conn.close()

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\nTechnical analysis completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {duration}")
    print(f"Results saved to 'technical_indicators' table in {database_path}")


if __name__ == "__main__":
    DATABASE_PATH = "mse_stocks.db"
    technical_analysis(DATABASE_PATH)