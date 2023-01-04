import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
plt.style.use('dark_background')

stock_list = ['AAPL', 'MSFT', 'TSLA', 'KO', 'INTC', 'AMZN', 'AMD', 'PG', 'META', 'NVDA', 'GOOG']
etf_list = ['VTI', 'QQQ', 'VIG', 'HDV', 'SPYD', 'VYM', 'VOO', 'SPY', 'IVV']


def get_and_pickle_dividends(ticker_list):
# can use period="1mo", interval = "1wk"
    for ticker in ticker_list:
        dividends = yf.Ticker(ticker).dividends
        pd.to_pickle(dividends, f'{ticker}_dividends.pkl')

def get_and_pickle_ticker_history_data(ticker_list, output_file, period='max'):
    data = yf.download(ticker_list, period)
    pd.to_pickle(data, output_file)


def plot_all_close_prices(pickle_file_name):
    data = pd.read_pickle(pickle_file_name)
    data['Close'].plot()
    plt.show()

def plot_dividend_values(pickle_file_name):
    data = pd.read_pickle(pickle_file_name)
    data.plot()
    plt.show()


#plot_all_close_prices('./data/US_stocks_max.pkl')
plot_dividend_values('./data/SPYD_dividends.pkl')

# growth calc
#start = int(data['Close'][0])
#end = int(data['Close'][-1])
#print(start)
#print(end)
#ratio = 100*(end/start)
#growth = -1*(100 - ratio) if ratio < 100 else ratio - 100
#print(f'{growth}%')
