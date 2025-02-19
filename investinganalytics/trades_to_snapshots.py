import pandas as pd
import os
from .zerodha import holdings_reader

class Snapshots:
    def __init__(self):
        self.snapshots = {}

    def add(self, some_date, value):
        self.snapshots[some_date] = value
    
    def get_closest_previous_snapshot(self, some_date):
        # TODO: need to convert this to pandas dataframe to efficiently support this operation
        return self.snapshots[some_date]['snapshot']

# need to distinguish Snapshot with  a holding, need to think of a good domain model
class Snapshot:
    def __init__(self):
        self.df = pd.DataFrame(index=pd.Index([], name='symbol', dtype=str), columns=['quantity'])
    
    def update(self, symbol, quantity):
        if symbol in self.df.index:
            self.df.loc[symbol, 'quantity'] += quantity  # Direct DataFrame update
        else:
            self.df.loc[symbol, 'quantity'] = quantity
    
        if self.df.loc[symbol, 'quantity'] == 0:
            self.remove(symbol)
        elif self.df.loc[symbol, 'quantity'] < 0:
            print('ERROR: quantity has become negative which is not possible')

    def remove(self, symbol):
        self.df.drop(symbol, inplace=True)
    
    def copy(self):
        # Create a new empty snapshot
        new_snapshot = Snapshot()
        new_snapshot.df = self.df.copy()
        return new_snapshot
    
    def print(self):
        print('------  snapshot is ---------')
        pd.options.display.max_rows = None
        print(self.df.sort_index())
            
    def get_or_create_row(self, symbol):
        print('here')
        if symbol in self.df.index:
            return self.df.loc[symbol]  # Return existing row
        else:
            new_row = pd.Series({'quantity': 0}, name=symbol)
            self.df.loc[symbol] = new_row
            return self.df.loc[symbol] # Return the newly created row

def convert(trades):
    """
    Format of Snapshot data
    """
    snapshots = Snapshots()
    start_date = trades['trade_date'].min()
    print('The portfolio started on date: ', start_date)

    # Sort the trades, as we will apply the trades over a previous snapshot (to avoid complete recalcultion)
    trades = trades.sort_values('trade_date')
    previous_snapshot = Snapshot()

    # Iterate through the groups (which will be in sorted date order)
    for trade_date, day_trades in trades.groupby('trade_date'):
        print(f"For Trade Date: {trade_date}")
        print(day_trades)
        current_snapshot = apply_trades(previous_snapshot.copy(), day_trades)
        current_snapshot.print()
        previous_snapshot = current_snapshot
        snapshots.add(trade_date, {
            'snapshot': current_snapshot,
            'cashflow_in': cashflows_in(trades),
            'cashflow_out': cashflows_out(trades)
        })
    
    return snapshots

def apply_trades(snapshot, trades):
    for index, trade in trades.iterrows():
        apply_trade(snapshot, trade)
    
    return snapshot

def apply_trade(snapshot, trade):
    symbol = trade['symbol']
    print('@prak - for symbol - ', symbol)
    if trade['trade_type'] == 'buy':
        snapshot.update(symbol, trade['quantity'])
    elif trade['trade_type'] == 'sell':
        quantity = trade['quantity'] * -1
        snapshot.update(symbol, quantity)
    else:
        print('WARN: trade_type found except buy or sell')
        
def cashflows_in(trades):
    buy_trades = trades[trades['trade_type'] == 'buy']
    if not buy_trades.empty:
        return (buy_trades['quantity'] * buy_trades['price']).sum()
    else:
        return 0.0

def cashflows_out(trades):
    sell_trades = trades[trades['trade_type'] == 'sell']
    if not sell_trades.empty:
        return (sell_trades['quantity'] * sell_trades['price']).sum()
    else:
        return 0.0
    
if __name__ == "__main__":  # This ensures the code only runs when the script is executed directly
    holdings = "holdings.csv"  
    holdings = holdings_reader.getHoldingsAsSellTrades(os.path.join('prakash', 'holdings.csv'))
    print(convert(holdings))