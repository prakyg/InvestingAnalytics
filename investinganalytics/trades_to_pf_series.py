import pandas as pd
from datetime import datetime, date, timedelta
def createSnapshots(trades, snapshots, stock_history_database):
    """
    For each date the market is open, the portfolio changes due to stock price movements
    We can calculate:
    1. Portfolio value on close of that day (need stock close price)
    2. Average P/E of the pf (need P/E)
    3. Any cash generated (via sell transactions)
    4. 

    So a pandas dataframe can be returned 
    with Index = Date
    Columns = Value, Cashflow out, P/E
    
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
    portfolio_history = {}
    start_date = trades['trade_date'].min()
    print('Start date: ', start_date)
    
    current_date = start_date

    # we will take start_date - 1 as the portfolio inception date
    portfolio_inception_date = start_date - timedelta(days=1)
    portfolio_history[portfolio_inception_date] = {
        'value': 0
        # can add other stuff like p/e here
    }
    interval = 1
    while (current_date <= date.today()):
        portfolio_history[portfolio_inception_date] = get_pf_data(current_date)
        current_date += timedelta(days=interval)

    return portfolio_history

def get_pf_data(snapshots, stock_history_database, curr_date):
    print('Creating portfolio snapshot for date:', curr_date)
    ## get all rows where trade_date > last_snapshot_date but <= current_date , TODO:
    ## for now constructing from start_date each time
    snapshot_on_curr_date = snapshots.get_closest_previous_snapshot(curr_date)
    curr_value = snapshot_to_current_value(snapshot_on_curr_date, stock_history_database)
    return {
        'value': curr_value
    }

def snapshot_to_current_value(snapshot, stock_history_database, curr_date):
    ToDo
    #totalValue = 0
    #for symbol, quantity in snapshot:
    #    totalValue += stock_history_database[symbol][curr_date].closePrice * quantity