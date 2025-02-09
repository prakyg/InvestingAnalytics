import pandas as pd
from pyxirr import xirr
import glob
import os
from datetime import datetime, timedelta, date
from tabulate import tabulate
import sys
import yfinance as yf

"""
This program calculates XIRR.
XIRR can be calculated for a single stock or the entire portfolio.

Program can be run as follows: python3 xirr_filter_multiple.py <directory-name>
directory-name: should contain the investing data
There should be 2 types of data
1. Tradebooks: Should contain the following columns: symbol, trade_date, trade_type, quantity, price
               Filename should in the following format: tradebook-*.csv
               Tradebooks downloaded from zerodha work out of the box.
2. Current state of holdings: symbol, quantity, price
               Filename should be holdings.csv
               Holdings.csv downloaded from zerodha works out of the box.

Note:
TODOS: 1. In a future version of this program, we would be able to fetch price from an API negating the need for
holdings.csv
2. holdings.csv should not need quantity which can be calculated from tradebook. However it is useful to detect
discrepancies due to things like buybacks, gifting of shares, symbol changes, rights etc

Dependencies: Your python env should have pandas module installed.


"""
def calculate_xirr_portfolio(data, corporateActionsData, presentValue = None):
    """
    This program calculates XIRR.
    XIRR can be calculated for a single stock or the entire portfolio.

    Args:
        data: A pandas DataFrame containing trade data.

    Returns:
        A dictionary containing XIRR for the stock or portfolio and a list of symbols with negative cashflows.
    """
    cashflows = []
    for index, row in data.iterrows():
        # Consider only buy (negative) and sell (positive) transactions
        if row['trade_type'].lower() in ["buy", "sell"]:
            # Adjust cashflow for quantity and price
            consideration = row['quantity'] * row['price']
            cashflow = consideration * -1 if row['trade_type'].lower() == "buy" else consideration
            # Adjust for trade date (assuming trade_date is a datetime format)
            cashflows.append((row['trade_date'], cashflow))
            # Check for at least one sell transaction
        else:
            print("WARNING: A row is found with trade_type != buy or sell")
    if len(data.index) != len(cashflows):
        print(f"ERROR: Mismatch in entries in 'data' and 'cashflows'")

    if presentValue:
        cashflows.append((datetime.now().strftime("%Y-%m-%d"), presentValue))
    xirr_results = xirr(cashflows)

    return {'xirr': xirr_results}

def validate_quantity(symbol, group_data):
    #print(group_data)
    buy_quantity = 0
    sell_quantity = 0
    for index, row in group_data.iterrows():
        if row['trade_type'].lower() == "buy":
            buy_quantity = buy_quantity + row['quantity']
        else:
            sell_quantity = sell_quantity + row['quantity']
    if buy_quantity != sell_quantity:
        print(f"For symbol: {symbol}, buy quantity ({buy_quantity}) !=  sell quantity ({sell_quantity})")


def calculate_xirr_stock(data, corporateActionsData, mode, target_stock):
    """
    Calculates XIRR for a single stock or the entire portfolio.

    Args:
        data: A pandas DataFrame containing trade data.

    Returns:
        A dictionary containing XIRR for the stock or portfolio and a list of symbols with negative cashflows.
    """
    symbols_with_no_buys = []
    symbols_with_no_sells = []

    if data['trade_type'].str.contains("sell").any():
        # Group data by symbol and calculate XIRR for each
        grouped_data = data.groupby('symbol')
        xirr_results = {}
        for symbol, group_data in grouped_data:
            if mode == 'trade_history':
                if target_stock == symbol:
                    print("Calculating for :" + symbol)
                    print(group_data.sort_values(by='trade_date', ascending=True))
                else:
                    continue

            cashflows = []
            profit = 0
            total_acquisitions = 0
            xirr_val = None
            for index, row in group_data.iterrows():
                if row['trade_type'].lower() in ["buy", "sell"]:
                    # Adjust cashflow for quantity and price
                    consideration = row['quantity'] * row['price']
                    cashflow = consideration * -1 if row['trade_type'].lower() == "buy" else consideration
                    # Adjust for trade date (assuming trade_date is a datetime format)
                    cashflows.append((row['trade_date'], cashflow))
                    profit = profit + cashflow
                    if cashflow < 0:
                        total_acquisitions = total_acquisitions + cashflow

            validate_quantity(symbol, group_data)
            if all(row['trade_type'].lower() == "sell" for index, row in group_data.iterrows()):
                symbols_with_no_buys.append(symbol)
            elif all(row['trade_type'].lower() == "buy" for index, row in group_data.iterrows()):
                symbols_with_no_sells.append(symbol)
            else:
                xirr_val = xirr(cashflows)

            percent_return = 0
            if total_acquisitions != 0:
                percent_return = round((profit / (-1 * total_acquisitions)) * 100, 2)
            xirr_results[symbol] = {'xirr': xirr_val, 'profit': profit, 'return_made': percent_return}
    else:
        print('ERROR: There are 0 sell trades in the data')
        # No buy transactions, so no negative cashflows
        xirr_results = None
    return {'xirr': xirr_results, 'symbols_with_no_sells': symbols_with_no_sells, 'symbols_with_no_buys':symbols_with_no_buys}

# Apply function to trim strings
def trim_hyphen_suffix(text):
    return text.split('-')[0]  # Split on hyphen and return the first part (AEL)

"""
The snapshot structure is as follows:
# type: pandas dataframe
    {
        'date': [2024-01-01, .....],
        'totalValue': [],
        'AveragePE': [],
        any other consolidated metrics
        #TODO holdings: []
    }

Holdings will have:
    {Stock, quantity, close price}
"""
def createSnapshots(tradebook, stock_history_database):
    snapshots = {}
    #TODO: do this in the data prep step
    tradebook['trade_date'] = pd.to_datetime(tradebook['trade_date']).dt.date
    start_date = tradebook['trade_date'].min()
    print('Start date: ', start_date)
    print('type = ', type(start_date))
    current_date = start_date
    print ('type now', type(datetime.today()))

    # we will take start_date - 1 as the portfolio inception date
    portfolio_inception_date = start_date - timedelta(days=1)
    snapshots[portfolio_inception_date] = [0]
    last_snapshot_date = portfolio_inception_date
    interval = 30
    while (current_date <= date.today()):
        print('Creating portfolio snapshot for date:', current_date)
        ## get all rows where trade_date > last_snapshot_date but <= current_date , TODO:
        ## for now constructing from start_date each time
        df_trades_before_current_date = tradebook[tradebook['trade_date'] <= current_date].copy()
        print('----@----@---', df_trades_before_current_date)
        df_trades_before_current_date['quantity'] = df_trades_before_current_date.apply(lambda row: row['quantity'] if row['trade_type'].upper() == 'BUY' else -row['quantity'], axis=1)
        print('after quantity check', df_trades_before_current_date)
        df_portfolio = df_trades_before_current_date.groupby('symbol')['quantity'].sum().reset_index()
        print('consolidated', df_portfolio)
        df_portfolio = df_portfolio[df_portfolio['quantity'] != 0]
        print('removed 0', df_portfolio)

        if not df_portfolio.empty:
            df_portfolio['market_value'] = 0.0
            for index, row in df_portfolio.iterrows():
                close_price = get_close_price(row['symbol'], current_date, stock_history_database)
                if close_price is None:
                    print(f"Warning: Could not retrieve close price for {row['symbol']} on {current_date}")
                    continue #ignore stocks where price data is not present
                print('got close price as', close_price)
                df_portfolio.loc[index, 'market_value'] = row['quantity'] * close_price
            snapshots[current_date] = df_portfolio
            print('snapshot has been created', df_portfolio)
        current_date += timedelta(days=interval)

    return snapshots

def get_close_price(symbol, date, stock_history_database):
    try:
        stock_history = stock_history_database[symbol]
        print(stock_history)
        price = stock_history.loc[date, 'Close']
        return price
    except:
        return None

def row_transformations(data):
    data['symbol'] = data['symbol'].apply(trim_hyphen_suffix)
    data['symbol'] = data['symbol'].replace('DEEPAKNI', 'DEEPAKNTR')
    data['symbol'] = data['symbol'].replace('CAPPL', 'CAPLIPOINT')
    data['symbol'] = data['symbol'].replace('LINCOPH', 'LINCOLN')
    data['symbol'] = data['symbol'].replace('SALZER', 'SALZERELEC')
    data['symbol'] = data['symbol'].replace('PREMEXPLQ', 'PREMEXPLN')
    data['symbol'] = data['symbol'].replace('INOXLEISUR', 'PVRINOX')
    data['symbol'] = data['symbol'].replace('COMPUAGE', 'COMPINFO')
    data['symbol'] = data['symbol'].replace('SHBCLQ', 'SBCL')
    data['symbol'] = data['symbol'].replace('PHILIPCARB', 'PCBL')
    data['symbol'] = data['symbol'].replace('JYOTI', 'JYOTISTRUC')
    data['symbol'] = data['symbol'].replace('TIPSINDLTD', 'TIPSMUSIC')
    data['symbol'] = data['symbol'].replace('LTI', 'LTIM')
    data['symbol'] = data['symbol'].replace('DHARAMSI', 'DMCC')
    data['symbol'] = data['symbol'].replace('IBULHSGFIN', 'SAMMAANCAP')
    return data

# Define a function to read and process all CSV files
# Returns a pandas dataframe containing the following columns:
# symbol -
# trade_date -
# trade_type -
# quantity -
# price -
def process_tradebooks(folder_name, file_pattern):
    all_data = pd.DataFrame()
    for filename in glob.glob(os.path.join(folder_name, file_pattern)):
        data = readFromFileSystem(filename)
        all_data = pd.concat([all_data, data])

    all_data = row_transformations(all_data)
    print(all_data)
    # Drop unnecessary columns
    columns_to_keep = ['symbol', 'trade_date', 'trade_type', 'quantity', 'price']
    all_data = all_data[columns_to_keep]
    print(all_data)

    return all_data

def process_holdings(filename):
    holdings_data = readFromFileSystem(filename)
    # Rename columns in holdings file of zerodha to the format of tradebooks
    holdings_data.rename(columns = {'Instrument':'symbol', 'Qty.': 'quantity', 'LTP':'price'}, inplace = True)
    holdings_data = row_transformations(holdings_data)

    # Drop unnecessary columns
    columns_to_keep = ['symbol', 'quantity', 'price']
    holdings_data = holdings_data[columns_to_keep]

    # Assume that all holding are being realized today, so insert columns of trade_type and trade_date
    holdings_data['trade_date'] = datetime.now().strftime("%Y-%m-%d")
    holdings_data['trade_type'] = 'sell'
    return holdings_data

def process_corporate_actions(filename):
    corporate_actions_data = readFromFileSystem(filename)
    print(corporate_actions_data)
    return corporate_actions_data

def readFromFileSystem(filename):
    print('Reading file: ' + filename)
    return pd.read_csv(filename)

#TODO
def print2Precision(num):
    return 1

def getStocksHistory(symbols):
    stock_history_database = []
    print('Stock universe of portfolio:', symbols)
    for symbol in symbols:
        symbol_history = getStockDataFromYahooFinance(symbol, ".NS")
        if symbol_history.empty:
            print('Retrying: Find the stock on BSE...')
            symbol_history = getStockDataFromYahooFinance(symbol, ".BO")

        if symbol_history.empty:
            print('Data not found on BSE as well, this stock will be skipped')
            continue

        # Convert timestamps to dates
        symbol_history.index = symbol_history.index.date
        symbol_history.to_csv(symbol + '_history_database.txt')
        symbol_history.to_excel(symbol + '_e_history_database.xlsx')
        stock_history_database.append([symbol, symbol_history])

    df = pd.DataFrame(stock_history_database, columns=['symbol', 'history'])
    df.set_index('symbol')
    return df

"""
This method returns historical data of a stock as a Pandas DataFrame
Format:
Date, Open, Close, High, Low, Volume, Dividends, Stock Splits
The index of the dataframe is 'Date' as opposed to row numbers.
"""
def getStockDataFromYahooFinance(symbol, suffix):
    yfinance_symbol = symbol + suffix
    try:
        ticker = yf.Ticker(yfinance_symbol)
        # Get historical data
        print('Fetching historical data for symbol: ', yfinance_symbol)
        hist = ticker.history(period="max", interval='1d')
    except Exception as e:
        print('An exception occured while trying to fetch data from yahoo finance', e)

    return hist

# Specify the pattern for your CSV files (replace with your pattern)
folder_name = sys.argv[1]
mode: str = 'xirr'
target_stock : str = ''
if len(sys.argv) > 2:
    mode = sys.argv[2]
if mode == 'trade_history':
    target_stock = sys.argv[3]

print("Tradebook directory specified as: ", folder_name)
print("Operating in mode: ", mode)
tradebook_file_pattern = "tradebook-*.csv"
holdings_file = 'holdings.csv'
corporate_actions_file = 'corporate-actions.csv'

# Read data from all CSV files
tradebookData = process_tradebooks(folder_name, tradebook_file_pattern)
holdingsData = process_holdings(os.path.join(folder_name, holdings_file))
corporateActionsData = process_corporate_actions(os.path.join(folder_name, corporate_actions_file))

# Calculate XIRR
#currentValueOfPortfolio = 8071742
#pfResults_withPresentValue = calculate_xirr_portfolio(tradebookData.copy(), currentValueOfPortfolio)
#print(f"Portfolio XIRR (on basis of present value): {pfResults_withPresentValue['xirr']:.2%}")

## merge holdings data with trade data
merged_data = pd.concat([tradebookData, holdingsData])
if len(tradebookData) + len(holdingsData) != len(merged_data):
    print("ERROR: merging of holdings data with tradebook data resulted in mismatch of rows")


# Download information about all portfolio stocks from yahoo finance APIs
all_unique_symbols = merged_data['symbol'].unique()
#stock_history_database = getStocksHistory(all_unique_symbols)
#stock_history_database = getStocksHistory(['SHAKTIPUMP'])
#stock_history_database.to_csv('stock_history_database.txt')
#stock_history_database.to_excel('e_stock_history_database.xlsx')
#df = pd.read_csv('stock_history_database.txt')
#e_df = pd.read_excel('e_stock_history_database.xlsx')
#if e_df.equals(stock_history_database):
#    print("DataFrames are equal.")
#else:
#    print("DataFrames are not equal.")

#if df.equals(stock_history_database):
#    print("DataFrames are equal txt.")
#else:
#    print("DataFrames are not equal txt.")


#stock_history_database = getStocksHistory(["FROG"])
#print(stock_history_database.head())
#get_close_price('MAPMYINDIA', date.fromisoformat("2024-12-20"), stock_history_database)
#createSnapshots(merged_data, stock_history_database)

stock_wise_results = calculate_xirr_stock(merged_data.copy(), corporateActionsData, mode, target_stock)

if (mode == 'xirr'):
    pfResults = calculate_xirr_portfolio(merged_data.copy(), corporateActionsData)
    print(f"Portfolio XIRR: {pfResults['xirr']:.2%}")

    if stock_wise_results['xirr'] is None:
        # This should not be possible as we consider present value of holdings as sell txn
        print("No sell transactions found in any of the CSV files.")
        sys.exit(0)

# Print XIRR for each stock (if available)
print("XIRR for individual stocks:")
df = pd.DataFrame(stock_wise_results['xirr'])
# transposed index (key as first column)
df = df.T
# Set options to display all rows and columns without truncation
pd.set_option('display.max_rows', None)

# Print the DataFrame with
print(df)

if df.size > 10:
    # Sort the DataFrame by 'Age' in ascending order (optional, specify descending order with ascending=False)
    sorted_df = df.sort_values(by='profit')
    print('\n----- Top 10 Absolute Profit trades -----\n')
    print(sorted_df.tail(10))
    print('\n----- Top 10 Absolute Loss trades -----\n')
    print(sorted_df.head(10))

    sorted_df = df.sort_values(by='return_made')
    print('\n--- Top 10 % returns trades -----\n')
    print(sorted_df.tail(10))
    print('\n----- Top 10 % loss trades -----\n')
    print(sorted_df.head(10))

# Print list of symbols with negative cashflows (if any)
if stock_wise_results['symbols_with_no_sells']:
    print("\nsymbols_with_no_sells (XIRR not calculated):")
    print(", ".join(stock_wise_results['symbols_with_no_sells']))

if stock_wise_results['symbols_with_no_buys']:
    print("\nsymbols_with_no_buys (XIRR not calculated):")
    print(", ".join(stock_wise_results['symbols_with_no_buys']))