# InvestingAnalytics

Get the XIRR of your portfolio constructed from your tradebook.

Currently only supports Zerodha, but other brokers can be supported very easily.

## How to run?
Download this repo and run it via python3:
python3 ./xirr_filter_multiple.py <folder-name>

In the <folder-name>, add all the downloaded tradebooks from zerodha in CSV format.
Add an empty csv named 'corporate-actions.csv'. TODO: Fix in next commit
Add the holdings.csv file (you can download from the kite web Holdings page)

To calculate XIRR, we assume that all your holdings are sold on the day script is run. So if your holdings 
are old, while script is run at a later date, this might make your XIRR slightly lower as period has become longer.

## How to handle stock symbol changes?
Many times stock symbol gets changed by companies. Like HBL Power Systems changed its name to HBL Engineering. Its symbol was changed from HBLPOWER to HBLENGINE. To accomodate for this transformation, manual entries need to be done in the aliases.csv file in the resources folder before running the program.

## Python Module Dependencies
pandas
pyxirr
tabulate
yfinance

P.S. Don't inspect the code just yet.
