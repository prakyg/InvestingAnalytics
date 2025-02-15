import pandas as pd
from datetime import datetime, timedelta, date

def convert(trades):
    snapshots = {}
    start_date = trades['trade_date'].min()
    print('The portfolio started on date: ', start_date)

    # Sort the DataFrame by 'trade_date' (important for ordered iteration)
    trades = trades.sort_values('trade_date')
    previous_snapshot = pd.DataFrame(index=pd.Index([], name='symbol', dtype=str), columns=['quantity'])

    # we will take start_date - 1 as the portfolio inception date
    #portfolio_inception_date = start_date - timedelta(days=1)
    #snapshots[portfolio_inception_date] = previous_snapshot

    # Iterate through the groups (which will be in sorted date order)
    for trade_date, day_trades in trades.groupby('trade_date'):
        print(f"For Trade Date: {trade_date}")
        print(day_trades)
        current_snapshot = apply_trades(previous_snapshot.copy(), day_trades)
        print('------  snapshot is ---------')
        pd.options.display.max_rows = None
        print(current_snapshot.sort_index())
        previous_snapshot = current_snapshot
        snapshots[trade_date] = current_snapshot
    
    return snapshots

def apply_trades(snapshot, trades):
    for index, trade in trades.iterrows():
        apply_trade(snapshot, trade)
    
    return snapshot

def apply_trade(snapshot, trade):
    symbol = trade['symbol']
    holding_row_for_symbol = get_or_create_row(snapshot, symbol)
    if trade['trade_type'] == 'buy':
        holding_row_for_symbol['quantity'] += trade['quantity']
    elif trade['trade_type'] == 'sell':
        holding_row_for_symbol['quantity'] -= trade['quantity']
    else:
        print('WARN: trade_type found except buy or sell')

    if holding_row_for_symbol['quantity'] == 0:
        snapshot.drop(symbol, inplace=True)
    if holding_row_for_symbol['quantity'] < 0:
        print('ERROR: quantity has become negative which is not possible')

def get_or_create_row(df, symbol):
    if symbol in df.index:
        return df.loc[symbol]  # Return existing row
    else:
        new_row = pd.Series({'quantity': 0}, name=symbol)
        df.loc[symbol] = new_row
        return df.loc[symbol] # Return the newly created row