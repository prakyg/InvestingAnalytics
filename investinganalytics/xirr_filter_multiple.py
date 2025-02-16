import pandas as pd
from pyxirr import xirr
from datetime import datetime
from tabulate import tabulate
import sys
from . import trades_to_snapshots
from .zerodha import tradebooks_reader
from .zerodha import holdings_reader
import os
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
"""
def trades_to_cashflows(trades):
    cashflows = []
    count_buys = 0
    count_buys_plus_sells = 0
    for index, trade in trades.iterrows():
        count_buys_plus_sells += 1
        # Consider only buy (negative) and sell (positive) transactions
        if not trade['trade_type'].lower() in ['buy', 'sell']:
            print('WARN: Skipping row found with trade_type != buy / sell')
            continue
        
        # Adjust cashflow for quantity and price
        cashflow = trade['quantity'] * trade['price']
        if trade['trade_type'].lower() == 'buy':
            count_buys += 1;
            cashflow = cashflow * -1

        cashflows.append((trade['trade_date'], cashflow))
        # Check for at least one sell transaction

    if len(trades.index) != len(cashflows):
        print('DEBUG: Mismatch in entries in trades and cashflows')

    return {
        'cashflows': cashflows,
        'has_one_buy': count_buys > 0,
        'has_one_sell': (count_buys_plus_sells - count_buys) > 0
    }

def calculate_xirr(trades, presentValue = None):
    """
    This program calculates XIRR.
    XIRR can be calculated for a single stock or the entire portfolio.

    Args:
        data: A pandas DataFrame containing trade data.

    Returns:
        A dictionary containing XIRR for the stock or portfolio and a list of symbols with negative cashflows.
    """
    if not trades['trade_type'].str.contains('sell').any():
        print('WARN: No SELL trades found')
        return {'xirr': None}

    cashflows = trades_to_cashflows(trades)['cashflows']

    if presentValue:
        cashflows.append((datetime.now().strftime("%Y-%m-%d"), presentValue))
    xirr_results = xirr(cashflows)

    return {'xirr': xirr_results}

def validate_quantity(symbol, symbol_trades):
    #print(group_data)
    buy_quantity = 0
    sell_quantity = 0
    for index, trade in symbol_trades.iterrows():
        if trade['trade_type'].lower() == "buy":
            buy_quantity = buy_quantity + trade['quantity']
        else:
            sell_quantity = sell_quantity + trade['quantity']
    if buy_quantity != sell_quantity:
        print(f"For symbol: {symbol}, buy quantity ({buy_quantity}) !=  sell quantity ({sell_quantity})")


def calculate_xirr_stock(trades, mode, target_stock):
    """
    Calculates XIRR for a single stock or the entire portfolio.

    Args:
        data: A pandas DataFrame containing trade data.

    Returns:
        A dictionary containing XIRR for the stock or portfolio and a list of symbols with negative cashflows.
    """
    symbols_with_no_buys = []
    symbols_with_no_sells = []

    if trades['trade_type'].str.contains("sell").any():
        # Group data by symbol and calculate XIRR for each
        grouped_trades = trades.groupby('symbol')
        xirr_results = {}
        for symbol, symbol_trades in grouped_trades:
            if mode == 'trade_history':
                if target_stock == symbol:
                    print("Calculating for :" + symbol)
                    print(symbol_trades.sort_values(by='trade_date', ascending=True))
                else:
                    continue

            res = trades_to_cashflows(symbol_trades)
            symbol_cashflows = res['cashflows']
            
            profit = 0
            total_acquisitions = 0
            for cashflow in symbol_cashflows:
                profit += cashflow[1]
                if cashflow[1] < 0:
                    total_acquisitions = total_acquisitions + cashflow[1]

            validate_quantity(symbol, symbol_trades)
            xirr_val = None
            if not res['has_one_buy']:
                symbols_with_no_buys.append(symbol)
            elif not res['has_one_sell']:
                symbols_with_no_sells.append(symbol)
            else:
                xirr_val = xirr(symbol_cashflows)

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

def my_main(folder_name, mode, target_stock):
    verbose = True
    print("INFO: Tradebook directory specified as: ", folder_name)
    print("INFO: Operating in mode: ", mode)
    tradebook_file_pattern = "tradebook-*.csv"
    holdings_file = 'holdings.csv'
    corporate_actions_file = 'resources/corporate-actions.csv'

    # Read data from all CSV files
    tradebooks = tradebooks_reader.getTrades(folder_name, tradebook_file_pattern, verbose)
    holdings = holdings_reader.getHoldingsAsSellTrades(os.path.join(folder_name, holdings_file), verbose)
    corporateActionsData = process_corporate_actions(corporate_actions_file)

    # Calculate XIRR
    #currentValueOfPortfolio = 8071742
    #pfResults_withPresentValue = calculate_xirr(tradebookData.copy(), currentValueOfPortfolio)
    #print(f"Portfolio XIRR (on basis of present value): {pfResults_withPresentValue['xirr']:.2%}")

    ## merge holdings data with trade data
    trades = pd.concat([tradebooks, holdings])
    if len(tradebooks) + len(holdings) != len(trades):
        print("ERROR: merging of holdings data with tradebook data resulted in mismatch of rows")

    # Download information about all portfolio stocks from yahoo finance APIs
    all_unique_symbols = trades['symbol'].unique()
    #stock_history_database = getStocksHistory(all_unique_symbols)
    
    #createSnapshots(merged_data, stock_history_database)

    stock_wise_results = calculate_xirr_stock(trades.copy(), mode, target_stock)

    if (mode == 'xirr'):
        pfResults = calculate_xirr(trades.copy())
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