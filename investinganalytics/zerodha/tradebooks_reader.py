import pandas as pd
import glob
import os
from .. import alias_reader

# Apply function to trim strings
def trim_hyphen_suffix(text):
    return text.split('-')[0]  # Split on hyphen and return the first part (AEL)

def row_transformations(data):
    data['symbol'] = data['symbol'].apply(trim_hyphen_suffix)
    for oldname, newname in alias_reader.getAliases('resources/aliases.csv').items():
        print('DEBUG: Replacing ', oldname, ' with ', newname)
        data['symbol'] = data['symbol'].replace(oldname, newname)

    return data

def getTrades(dir, filename_pattern, verbose=False):
    """
    Read and process all files
    TODO: ignore non-csv
    Returns a pandas dataframe containing the following columns:
    symbol: The stock symbol such as INFY
    trade_date: Date on which trade occured <class 'datetime.date'>
    trade_type: 'buy' or 'sell'
    quantity: number of stocks that were part of the trade
    price: price at which trade occurred
    """
    trades = pd.DataFrame()
    for filename in glob.glob(os.path.join(dir, filename_pattern)):
        print('Reading file: ' + filename)
        data = pd.read_csv(filename)
        trades = pd.concat([trades, data])

    trades = row_transformations(trades)
    # keep only relevant columns
    columns_to_keep = ['symbol', 'trade_date', 'trade_type', 'quantity', 'price']
    trades = trades[columns_to_keep]
    trades['trade_date'] = pd.to_datetime(trades['trade_date']).dt.date
    if verbose:
        print('------- Trades Data ------')
        print(trades)

    return trades