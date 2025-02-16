import pandas as pd
from datetime import datetime, date, timedelta
def createSnapshots(trades, stock_history_database):
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
    snapshots = {}
    #TODO: do this in the data prep step
    trades['trade_date'] = pd.to_datetime(trades['trade_date']).dt.date
    start_date = trades['trade_date'].min()
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
        df_trades_before_current_date = trades[trades['trade_date'] <= current_date].copy()
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