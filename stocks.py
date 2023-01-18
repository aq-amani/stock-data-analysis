import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
plt.style.use('dark_background')

stock_list = ['AAPL', 'MSFT', 'TSLA', 'KO', 'INTC', 'AMZN', 'AMD', 'PG', 'META', 'NVDA', 'GOOG']
etf_list = ['VTI', 'QQQ', 'VIG', 'HDV', 'SPYD', 'VYM', 'VOO', 'SPY', 'IVV']
# Get JP stock list
JP_stocks = ['2897.T']
FX = ['USDJPY=X']

def jp_investing_csv_to_data_frame(csv_file):
    """To process CSV data obtained from
    https://jp.investing.com/currencies/usd-jpy-historical-data

    Arguments:
    csv_file -- filename string of the csv file
    """
    data = pd.read_csv(csv_file, index_col=0)
    # Change column names to those accepted by mplfinance
    data.columns = ['Close', 'Open', 'High', 'Low','Volume', 'Percent']
    data.index.names = ['Date']
    data.index = pd.to_datetime(data.index)
    # Reverse data order to have older entries first
    data = data.iloc[::-1]
    data = data.fillna(0)
    data['Volume'] = 0 # Set all volume to zero as it has strings like 0.01K..
    return data


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

def plot_candles_and_delta_pips(data, verbosity, chart_title, recent_point_count=50, pips_lines=True, profit_line=3, losscut_line=300):
    """Plots 3 charts per ticker: Price candle chart and delta PIPs bars for Close-Open and High-Low prices

    Arguments:
    data -- dataframe with price information
    verbosity -- string specifying data verbosity. Used to choose chart size settings ('week', 'minute', 'day')
    chart_title -- String to show on top of chart
    recent_point_count -- number of data points to plot counted backwards from the most recent data point
    pips_lines -- bool. Whether to plot lines specified by profit_line and losscut_line
    profit_line -- Only when pips_lines is True. Specify value for the pips delta charts to plot a line at
    losscut_line -- Only when pips_lines is True.Specify value for the pips delta charts to plot a line at
    """
    data = data[-recent_point_count:-1]
    bar_width = 0.0005 if verbosity == 'minute' else 3 if verbosity == 'week' else 0.5
    price_major_tick_multiplier = 0.1 if verbosity == 'minute' else 5
    price_minor_tick_multiplier = 0.05 if verbosity == 'minute' else 1
    delta_major_tick_multiplier = 0.02 if verbosity == 'minute' else 2
    delta_minor_tick_multiplier = 0.01 if verbosity == 'minute' else 0.5

    delta_major_tick_multiplier *= 100 # deltas in PIPs
    delta_minor_tick_multiplier *= 100 # deltas in PIPs

    candle_width = 2
    pips_line_width = 0.8
    # Making own style based on  nightclouds style
    my_market_colors = mpf.make_marketcolors(up='r',down='g', wick={'up':'r','down':'g'})
    my_style = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=my_market_colors)

    fig, ax = plt.subplots(3, 1, figsize=(12,8))
    fig.suptitle(f'{chart_title} latest {recent_point_count} points', fontsize=16)

    oc_deltas = (data['Close'] - data['Open']) * 100 # yen to PIPs
    peak_deltas = (data['High'] - data['Low']) * 100 # yen to PIPs
    if pips_lines:
        data[losscut_line] = losscut_line
        data[profit_line] = profit_line
    # Negative bars if the price decreased from Open to Close
    peak_deltas = peak_deltas.where(oc_deltas > 0, peak_deltas * -1)
    # ax[0] : Plot candle chart using custom style
    mpf.plot(data, type='candle', style=my_style, scale_width_adjustment=dict(candle=candle_width), ax=ax[0]) # can have figratio=(12,4) as an argument

    # ax[1] : Plot Open/Close deltas in PIPs
    ax[1].bar(oc_deltas.index, oc_deltas.values, width=bar_width)
    if pips_lines:
        ax[1].plot(data[profit_line], lw=pips_line_width, c='r', linestyle='dashed', label=f'±{profit_line} PIPs')
        ax[1].plot(-1*data[profit_line], lw=pips_line_width, c='r', linestyle='dashed')
        if (peak_deltas.abs()).max() > losscut_line - 10:
            ax[1].plot(data[losscut_line], lw=pips_line_width, c='magenta', linestyle='dashed', label=f'±{losscut_line} PIPs')
            ax[1].plot(-1*data[losscut_line], lw=pips_line_width, c='magenta', linestyle='dashed')
            ax[1].legend(loc='lower left')
    ax[1].set_ylabel('OC deltas (PIPs)')

    # ax[2] : Plot Max/Min deltas in PIPs
    ax[2].bar(peak_deltas.index, peak_deltas.values, width=bar_width)
    if pips_lines:
        ax[2].plot(data[profit_line], lw=pips_line_width, c='r', linestyle='dashed', label=f'±{profit_line} PIPs')
        ax[2].plot(-1*data[profit_line], lw=pips_line_width, c='r', linestyle='dashed')
        if (peak_deltas.abs()).max() > losscut_line - 10:
            ax[2].plot(data[losscut_line], lw=pips_line_width, c='magenta', linestyle='dashed', label=f'±{losscut_line} PIPs')
            ax[2].plot(-1*data[losscut_line], lw=pips_line_width, c='magenta', linestyle='dashed')
            ax[2].legend(loc='lower left')
    ax[2].set_ylabel('Peak deltas (PIPs)')

    ax[1].xaxis.set_tick_params(rotation=50)
    ax[2].xaxis.set_tick_params(rotation=50)

    ax[0].yaxis.set_major_locator(ticker.MultipleLocator(price_major_tick_multiplier))
    ax[0].yaxis.set_minor_locator(ticker.MultipleLocator(price_minor_tick_multiplier))
    ax[1].yaxis.set_major_locator(ticker.MultipleLocator(delta_major_tick_multiplier))
    ax[1].yaxis.set_minor_locator(ticker.MultipleLocator(delta_minor_tick_multiplier))
    ax[2].yaxis.set_major_locator(ticker.MultipleLocator(delta_major_tick_multiplier))
    ax[2].yaxis.set_minor_locator(ticker.MultipleLocator(delta_minor_tick_multiplier))
    ax[0].grid(axis='y',linestyle='dotted', lw=0.5)
    ax[1].grid(axis='y',linestyle='dotted', lw=0.5)
    ax[2].grid(axis='y',linestyle='dotted', lw=0.5)

    fig.tight_layout()
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
