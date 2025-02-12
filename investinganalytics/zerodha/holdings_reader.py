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
    # TODO: ideally holdings to sell transactions transformation should be done by a util
    print('Reading file: ', filename)
    holdings_data = pd.read_csv(filename)
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