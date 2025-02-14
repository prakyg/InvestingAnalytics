import pandas as pd
from .. import alias_reader
import os
from datetime import datetime

# Apply function to trim strings
def trim_hyphen_suffix(text):
    return text.split('-')[0]  # Split on hyphen and return the first part (AEL)

def row_transformations(data):
    data['symbol'] = data['symbol'].apply(trim_hyphen_suffix)
    for oldname, newname in alias_reader.getAliases('resources/aliases.csv').items():
        print('DEBUG: Replacing ', oldname, ' with ', newname)
        data['symbol'] = data['symbol'].replace(oldname, newname)

    return data

def getHoldingsAsSellTrades(filename, verbose=False):
    """
    Converts holdings to Sell trades
    Returns a Pandas Dataframe with the following columns:
    symbol: type string
    quantity: type integer
    price: price at which the transaction is done
    trade_type: a string with value = sell
    trade_date: <class 'datetime.date'>
    """
    # TODO: ideally holdings to sell transactions transformation should be done by a util
    print('INFO: Reading file: ', filename)
    holdings = pd.read_csv(filename)
    # Rename columns in holdings file of zerodha to the format of tradebooks
    holdings.rename(columns = {'Instrument':'symbol', 'Qty.': 'quantity', 'LTP':'price'}, inplace = True)
    holdings = row_transformations(holdings)

    # Drop unnecessary columns
    columns_to_keep = ['symbol', 'quantity', 'price']
    holdings = holdings[columns_to_keep]

    # Assume that all holding are being realized today, so insert columns of trade_type and trade_date
    holdings['trade_date'] = datetime.now().strftime("%Y-%m-%d")
    holdings['trade_date'] = pd.to_datetime(holdings['trade_date']).dt.date
    holdings['trade_type'] = 'sell'
    if verbose:
        print('------- Converted Holdings Data ------')
        print(holdings)
        
    return holdings