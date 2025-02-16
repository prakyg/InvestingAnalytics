import yfinance as yf
import pandas as pd
import traceback 
from datetime import date

class StocksHistory:
    def __init__(self, stock_history_database):
        self.stock_history_database = stock_history_database

    def get_close_price(self, symbol, date_str):
        iso_date = date.fromisoformat(date_str)
        try:
            stock_history = self.stock_history_database[symbol]
            price = stock_history.loc[iso_date, 'Close']
            print(f'price is {price}')
            return price
        except Exception as e:
            print(f"ERROR: An exception occurred: {e}")
            print(traceback.format_exc())
            return None

def fetch_stocks_history(symbols):
    """
    { symbol : history dataframe }
    """
    stock_history_database = {}
    print('Stock universe of portfolio: ', symbols)
    for symbol in symbols:
        symbol_data = fetch_symbol_data(symbol, ".NS")
        if not symbol_data:
            print('Retrying: Find the stock on BSE...')
            symbol_data = fetch_symbol_data(symbol, ".BO")

        if not symbol_data:
            print('Data not found on BSE as well, this stock will be skipped')
            continue
        
        symbol_history = get_history(symbol_data)        
        stock_history_database[symbol] = symbol_history

    return StocksHistory(stock_history_database)

def fetch_symbol_data(symbol, suffix):
    """
    This method returns historical data of a stock as a Pandas DataFrame
    Format:
    Date (index), OHLC, Volume, Dividends, Stock Splits

    The index of the dataframe is 'Date' as opposed to row numbers.
    Type of date is : 2002-08-12 00:00:00+05:30
    """
    yfinance_symbol = symbol + suffix
    ticker = yf.Ticker(yfinance_symbol)
    if not 'currentPrice' in ticker.info:
        return None
        
    # Print basic information about the Ticker object
    #print("Ticker Symbol:", ticker.ticker)  # "RELIANCE.NS"
    #print(ticker.info)
    #print(ticker.dividends)
    #print(ticker.splits)
    #print(ticker.actions)
    #print('Historical data: ')
    #hist = ticker.history(period="max", interval='1d')
    #print(hist)
    
    return ticker

def get_history(ticker):
    """
    This method returns historical data of a stock as a Pandas DataFrame
    Format:
    Date (index), OHLC, Volume, Dividends, Stock Splits

    The index of the dataframe is 'Date' as opposed to row numbers.
    Type of date is : 2002-08-12
    """
    hist = ticker.history(period="max", interval='1d')
    # Convert timestamps to dates
    hist.index = hist.index.date
    return hist

# Example usage:
if __name__ == "__main__":
    s = fetch_stocks_history(['TCS'])
    print (f'close price is {s.get_close_price('TCS', '2002-08-12')}')
    