import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import *
import math
plt.style.use('dark_background')

stock_list = ['AAPL', 'MSFT', 'TSLA', 'KO', 'INTC', 'AMZN', 'AMD', 'PG', 'META', 'NVDA', 'GOOG', 'JNJ', 'MRNA', 'PEP', 'WMT']
etf_list = ['VTI', 'QQQ', 'VIG', 'HDV', 'SPYD', 'VYM', 'VOO', 'SPY', 'IVV', 'BND', 'AGG', 'TLT']
# Get JP stock list
JP_stocks = ['2897.T']
FX = ['USDJPY=X']
# Make custom candle chart style based on nightclouds style
my_market_colors = mpf.make_marketcolors(up='r',down='g', wick={'up':'r','down':'g'})
my_style = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=my_market_colors)

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


def get_and_pickle_dividends(ticker_list, output_file):
    """Get historical dividend data through yfinance and save pickle file

    Arguments:
    ticker_list -- List of tickers of interest
    output_file -- filename string of output pickle file
    """
    ticker_dataframe_list = []
    for ticker in ticker_list:
        ticker_dataframe_list.append(yf.Ticker(ticker).dividends)
    data = pd.concat(ticker_dataframe_list, keys=ticker_list, axis=1)
    data = data.fillna(0)
    pd.to_pickle(data, output_file)

def get_and_pickle_ticker_history_data(ticker_list, output_file, period='max', interval='1d'):
    """Get historical ticker data through yfinance

    Arguments:
    ticker_list -- List of tickers of interest
    output_file -- filename string of output pickle file
    period -- Target period for the data to obtain
      -- valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    interval -- Data verbosity (daily, hourly..etc)
      -- valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
    """

    data = yf.download(ticker_list, period=period, interval=interval)
    if len(ticker_list) > 1:
        # Change yfinance data hierarchy from values-> tickers to tickers->values
        # To be able to index data by ticker name instead of price category (Open, Close..)
        # Only needed when requesting multiple tickers through yfinance
        data.columns = data.columns.swaplevel(0, 1)
        data.sort_index(axis=1, level=0, inplace=True)
    pd.to_pickle(data, output_file)

def plot_close_prices_comparison(data):
    """Plot line multiple candle charts for comparison

    Arguments:
    ticker_list -- list of ticker names
    base_filename -- common part of the filename between tickers
    """
    data = data.xs('Close', axis=1, level=1, drop_level=True)
    ax = data.plot(lw=1)
    ax.yaxis.set_major_locator(ticker.MultipleLocator( 100 * math.ceil(data.max().max() / 100)/10))
    ax.grid(axis='y',linestyle='dotted', lw=0.5)
    plt.show()

def plot_candles_and_delta_pips(data, chart_title, recent_point_count=50, pips_lines=True, profit_line=3, losscut_line=300):
    """Plots 3 charts per ticker: Price candle chart and delta PIPs bars for Close-Open and High-Low prices

    Arguments:
    data -- dataframe with price information
    chart_title -- String to show on top of chart
    recent_point_count -- number of data points to plot counted backwards from the most recent data point
    pips_lines -- bool. Whether to plot lines specified by profit_line and losscut_line
    profit_line -- Only when pips_lines is True. Specify value for the pips delta charts to plot a line at
    losscut_line -- Only when pips_lines is True.Specify value for the pips delta charts to plot a line at
    """
    data = data[-recent_point_count:-1]
    oc_deltas = (data['Close'] - data['Open']) * 100 # yen to PIPs
    peak_deltas = (data['High'] - data['Low']) * 100 # yen to PIPs
    if pips_lines:
        data[losscut_line] = losscut_line
        data[profit_line] = profit_line
    max_delta_value = peak_deltas.max()
    max_price_range = data['High'].max() - data['Low'].min()
    # Negative bars if the price decreased from Open to Close
    peak_deltas = peak_deltas.where(oc_deltas > 0, peak_deltas * -1)

    # Chart settings
    price_major_tick_multiplier = 10 * math.ceil(max_price_range / 10)/10
    price_minor_tick_multiplier = price_major_tick_multiplier/2
    delta_major_tick_multiplier = 100 * math.ceil(max_delta_value / 100)/5
    delta_minor_tick_multiplier = delta_major_tick_multiplier/2

    candle_width = 2
    pips_line_width = 0.8

    fig, ax = plt.subplots(3, 1, figsize=(12,8))
    fig.suptitle(f'{chart_title} latest {recent_point_count} points', fontsize=16)

    # ax[0] : Plot candle chart using custom style
    mpf.plot(data, type='candle', style=my_style, scale_width_adjustment=dict(candle=candle_width), ax=ax[0]) # can have figratio=(12,4) as an argument

    # ax[1] : Plot Open/Close deltas in PIPs
    ax[1].stem(oc_deltas.index, oc_deltas.values, markerfmt=" ", basefmt=" ")
    if pips_lines:
        ax[1].plot(data[profit_line], lw=pips_line_width, c='r', linestyle='dashed', label=f'±{profit_line} PIPs')
        ax[1].plot(-1*data[profit_line], lw=pips_line_width, c='r', linestyle='dashed')
        if (peak_deltas.abs()).max() > losscut_line - 10:
            ax[1].plot(data[losscut_line], lw=pips_line_width, c='magenta', linestyle='dashed', label=f'±{losscut_line} PIPs')
            ax[1].plot(-1*data[losscut_line], lw=pips_line_width, c='magenta', linestyle='dashed')
            ax[1].legend(loc='lower left')
    ax[1].set_ylabel('OC deltas (PIPs)')

    # ax[2] : Plot Max/Min deltas in PIPs
    ax[2].stem(peak_deltas.index, peak_deltas.values, markerfmt=" ", basefmt=" ")
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

def calculate_growth(data, start_datetime, end_datetime):
    """Calculate percentage of growth between two points in time

    Arguments:
    data -- datetime indexed dataframe
    start_datetime -- string of period start datetime (ex.:'2022-01-01 09:00:00')
    end_datetime -- string of period end datetime
    """
    data = data.loc[start_datetime:end_datetime]
    start = data['Close'][0]
    end = data['Close'][-1]
    ratio = 100*(end/start)
    growth = -1*(100 - ratio) if ratio < 100 else ratio - 100
    return growth

def compare_growth(data):
    """Calculate percentage of growth within the past years and months calculated from today

    Arguments:
    data -- datetime indexed dataframe containing ticker price data
    """
    # TODO: can be made more dynamic by passing the periods list as an argument
    ticker_list = list(data.columns.levels[0])
    growth_data = pd.DataFrame(columns=ticker_list, index=['5y', '3y', '1y', '6mo', '3mo', '1mo'])
    today = date.today()
    for ticker in ticker_list:
        growth_data.loc['5y'][ticker]= calculate_growth(data[ticker], today - relativedelta(years=5), today)
        growth_data.loc['3y'][ticker]= calculate_growth(data[ticker], today - relativedelta(years=3), today)
        growth_data.loc['1y'][ticker]= calculate_growth(data[ticker], today - relativedelta(years=1), today)
        growth_data.loc['6mo'][ticker] = calculate_growth(data[ticker], today - relativedelta(months=6), today)
        growth_data.loc['3mo'][ticker] = calculate_growth(data[ticker], today - relativedelta(months=3), today)
        growth_data.loc['1mo'][ticker] = calculate_growth(data[ticker], today - relativedelta(months=1), today)
    return growth_data

def get_data_by_datetime_range(data, start_datetime, end_datetime):
    """For datetime indexed dataframes. Returns entries in the specified datetime range

    Arguments:
    data -- datetime indexed dataframe
    start_datetime -- string of range start datetime (ex.:'2022-01-01 09:00:00')
    end_datetime -- string of range end datetime
    """
    return data.loc[start_datetime:end_datetime]

def plot_growth_comparison(data):
    """Bar plot for multiple tickers comparing growth over multiple periods

    Arguments:
    data -- datetime indexed dataframe fo growth percentages
    """
    ax = data.plot.bar(figsize=(14,8))
    ax.legend(loc='upper right')
    max_value = data.max().max()
    ax.yaxis.set_major_locator(ticker.MultipleLocator( 100 * math.ceil(max_value / 100)/20))
    ax.grid(axis='y',linestyle='dotted', lw=0.5)
    plt.show()

def plot_dividend_comparison(dividend_data, price_data):
    """Bar plot for multiple tickers comparing dividends over multiple periods

    Arguments:
    dividend_data -- datetime indexed dataframe
    price_data -- datetime indexed dataframe
    """
    # TODO: separate calculation and plotting
    # Group and sum dividend data by year
    dividend_data = dividend_data.groupby(dividend_data.index.year).sum()
    #dividend_data = dividend_data.fillna(0)
    # Use the Close price as the denominator
    price_data = price_data.xs('Close', axis=1, level=1, drop_level=True).groupby(price_data.index.year).mean()
    # Group and get mean of price data by year (can consider max/min too for a best/worst case calculations)
    #price_data = price_data.groupby(price_data.index.year).mean()
    # Calculate dividend yield%
    data = 100 * (dividend_data/ price_data)

    ax = data.plot.bar(figsize=(14,8))
    ax.legend(loc='upper right')
    max_value = data.max().max()
    ax.yaxis.set_major_locator(ticker.MultipleLocator( 10 * math.ceil(max_value / 10)/20))
    ax.grid(axis='y',linestyle='dotted', lw=0.5)
    plt.show()

def plot_multiple_candle_charts(ticker_list, base_filename):
    """Plot multiple candle charts for comparison

    Arguments:
    ticker_list -- list of ticker names
    base_filename -- common part of the CSV filename between tickers
    """
    #TODO: Decide base_filename assumptions
    ticker_dataframe_list = []
    for ticker in ticker_list:
        ticker_dataframe_list.append(jp_investing_csv_to_data_frame(f'./data/{ticker}{base_filename}'))
    data = pd.concat(ticker_dataframe_list, keys=ticker_list, axis=1)
    fig, ax = plt.subplots(len(fx_list), 1, figsize=(12,8))

    for idx, ticker in enumerate(ticker_list):
        mpf.plot(data[ticker], type='candle', style=my_style, scale_width_adjustment=dict(candle=2), ax=ax[idx])
        ax[idx].legend(labels=[ticker], loc='lower left')
    plt.show()

## Obtaining data from sources
##------------------------------
## Either get CSVs from https://jp.investing.com
## OR get data through yfinance (FX daily OC data is incorrect for at least USDJPY)
## Note: FX Daily Open and Close values are borked in yfinance
#period = '10y'
#interval = '1d'
#ticker_category = 'US_stocks'
#ticker_list = stock_list
#pickle_file_name = f'./data/{ticker_category}_P{period}_I{interval}_backfrom{date.today().strftime("%Y%m%d")}.pkl'
#get_and_pickle_ticker_history_data(ticker_list, pickle_file_name, period=period, interval=interval)
#data = pd.read_pickle(pickle_file_name)
## For dividends
#ticker_category = 'US_stocks_Dividends'
#ticker_list = stock_list
#pickle_file_name = f'./data/{ticker_category}_Pmax_Id_backfrom{date.today().strftime("%Y%m%d")}.pkl'
#get_and_pickle_dividends(ticker_list, pickle_file_name)
#data = pd.read_pickle(pickle_file_name)

## Comparison line plots of close prices for multiple tickers
## ----------------------------------------
#data = pd.read_pickle('./data/US_stocks_P10y_I1d_backfrom20230119.pkl')
#data = data.loc['2018-01-01':'2023-01-05']
#plot_close_prices_comparison(data)

## FX one currency candle and delta pips charts
## -------------------------------------------
#data = pd.read_pickle('./data/USD_JPY_P6mo_I1h_backfrom20230119.pkl')
#data = jp_investing_csv_to_data_frame(f'./data/USD_JPY_weekly_from20180101.csv')
#plot_candles_and_delta_pips(data, 'title here', recent_point_count=50, pips_lines=False, profit_line=3, losscut_line=70)

## Growth comparison chart
## -------------------------
#data = pd.read_pickle('./data/US_stocks_P10y_I1d_backfrom20230119.pkl')
#growth_data = compare_growth(data)
#plot_growth_comparison(growth_data)

## Dividend comparison chart
## ---------------------------
#ticker_category = 'US_ETFs'
#dividend_data = pd.read_pickle(f'./data/{ticker_category}_Dividends_Pmax_Id_backfrom20230119.pkl')
#price_data = pd.read_pickle(f'./data/{ticker_category}_P10y_I1d_backfrom20230119.pkl')
#dividend_data = dividend_data.loc['2013-01-01':'2023-01-01']
#plot_dividend_comparison(dividend_data, price_data)

## Multiple FX candle charts in parallel
## --------------------------------------
#fx_list = ['GBP', 'EUR', 'USD', 'NZD', 'AUD']
#plot_multiple_candle_charts(fx_list, base_filename='_JPY_weekly_from20180101.csv')
