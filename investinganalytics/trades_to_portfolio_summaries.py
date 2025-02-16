
def get(trades, snapshots, stocks_history):
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
    """
    return None