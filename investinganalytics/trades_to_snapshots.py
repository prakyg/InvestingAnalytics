import pandas as pd
from datetime import datetime, timedelta, date

class Snapshot:
    def __init__(self, val):
        self.val = val

def convert(trades):
    # A snapshot should contain: snapshot_date which can actually be the just the key
    # values need to be : symbol, qty , current_value actually can be computed with close_price so not needed
    # Other things important might be cashflows out, but do we really need that ?
    # cashflows can be constructed from the sell trades
    snapshots = {}
    start_date = trades['trade_date'].min()
    print('Start date: ', start_date)

    current_date = datetime.today()
    print ('type now', type(datetime.today()))

    # we will take start_date - 1 as the portfolio inception date
    portfolio_inception_date = start_date - timedelta(days=1)
    snapshots[portfolio_inception_date] = [0]

    # Sort the DataFrame by 'trade_date' (important for ordered iteration)
    trades = trades.sort_values('trade_date')

    # Iterate through the groups (which will be in sorted date order)
    snapshot = pd.DataFrame(index=pd.Index([], name='symbol', dtype=str), columns=['quantity'])
    for trade_date, day_trades in trades.groupby('trade_date'):
        print(f"For Trade Date: {trade_date}")
        print(day_trades)
        apply_trades(snapshot, day_trades)

    print('snapshot is ')
    print(snapshot)

def apply_trades(snapshot, trades):
    for index, trade in trades.iterrows():
        apply_trade(snapshot, trade)

def apply_trade(snapshot, trade):
    symbol = trade['symbol']
    holding_row_for_symbol = get_or_create_row(snapshot, symbol)
    if trade['trade_type'] == 'buy':
        holding_row_for_symbol['quantity'] += trade['quantity']
    elif trade['trade_type'] == 'sell':
        holding_row_for_symbol['quantity'] += trade['quantity']
    else:
        print('WARN: trade_type found except buy or sell')

    if holding_row_for_symbol['quantity'] == 0:
        snapshot = snapshot.drop(symbol)
    if holding_row_for_symbol['quantity'] < 0:
        print('ERROR: quantity has become negative which is not possible')

def get_or_create_row(df, symbol):
    if symbol in df.index:
        return df.loc[symbol]  # Return existing row
    else:
        new_row = pd.Series({'quantity': 0}, name=symbol)
        df.loc[symbol] = new_row
        return df.loc[symbol] # Return the newly created row