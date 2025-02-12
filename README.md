# InvestingAnalytics

Get the XIRR of your portfolio constructed from your tradebook.

Currently only supports Zerodha, but other brokers can be supported very easily.

## How to run?

### Running in Interactive mode (recommended for non-technical users)
Download this repo and run it via python3:
```
python3 ./xirr.py 
```

The program will ask you to enter the required information.

### Running in command-line mode
Download this repo and run it via python3:
```
python3 ./xirr.py <folder-name>
```

### Information about the arguments
In the <folder-name>:
1. Add all the downloaded tradebooks from zerodha in CSV format. The program specifically looks for file with `tradebook-*` pattern.
1. Add the `holdings.csv` file (you can download from the kite web Holdings page)

To calculate XIRR, we assume that all your holdings (from `holdings.csv`) are sold on the day script is run. So if your holdings 
are old, while script is run at a later date, this might make your XIRR slightly lower as period has become longer.

## Stock market events handling
### How to handle stock symbol changes?
Many times stock symbol gets changed by companies. Example, HBL Power Systems changed its symbol from HBLPOWER to HBLENGINE. To accomodate this, manual entries need to be done in the aliases.csv file in the resources folder before running the program. Feel free to contribute to the repo's aliases.csv file by raising a pull request.

### IPO allotments
Zerodha tradebook will have no buy entry. You can create a dummy tradebook where you can place a buy transaction for the ipo

### Stock splits, reverse splits and bonuses
These are handled automatically as price * qty remains the same.

### Rights issue, rights entitlement and partly-paid shares 
TODO: work in progress

### Mergers and demerges 
TODO: work in progress. Data will need to be supplied in the corporate-actions.csv file.

## Python Module Dependencies
pandas
pyxirr
tabulate
yfinance

P.S. Don't inspect the code just yet. It is a mess.
