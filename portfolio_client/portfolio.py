import time
from scraper import get_data_by_ticker
import requests
import tomllib

# Load configuration from the TOML file.
try:
   with open('config.toml', 'rb') as f:
       config = tomllib.load(f)
except Exception as e:
   print(f"Failed to load configuration: {e}")
   exit()

# Pull our entire portfolio as JSON from our server.
server_url = config['server']['url']
response = requests.get(server_url)
if response.status_code == 200:
    data = response.json()
else:
    print(f"Failed to fetch data. Server probably crashed. Status code: {response.status_code}. Did you rename portfolio_example.json to portfolio.json ?")
    exit()

# Updated in update_asset_data().
total_portfolio_value = 0
total_cash = 0

# Parse the portfolio JSON.
usd_owned = data['config']['cash']['usd_owned']
cad_owned = data['config']['cash']['cad_owned']

num_idv_divs = sum(1 for asset in data['assets'].values() if asset['type'] == 'idv_divs')
num_etf_divs = sum(1 for asset in data['assets'].values() if asset['type'] == 'etf_divs')
#num_yolos = sum(1 for asset in data['assets'].values() if asset['type'] == 'yolos')

pct_vt = data['config']['pcts']['pct_vt']
pct_voo = data['config']['pcts']['pct_voo']
pct_idv_divs = data['config']['pcts']['pct_idv_divs']
pct_etf_divs = data['config']['pcts']['pct_etf_divs']
pct_gold = data['config']['pcts']['pct_gold']
pct_btc = data['config']['pcts']['pct_btc']
#pct_yolos = data['config']['pcts']['pct_yolos']


# Build assets object
assets = {}

for ticker, info in data['assets'].items():
    asset_type = info['type']
    shares_owned = info['shares_owned']

    # JSON has type property so I can get pct this way.
    if asset_type == 'vt':
        percent = pct_vt
    elif asset_type == 'voo':
        percent = pct_voo
    elif asset_type == 'etf_divs':
        percent = pct_etf_divs / num_etf_divs
    elif asset_type == 'idv_divs':
        percent = pct_idv_divs / num_idv_divs
    #elif asset_type == 'yolos':
        #percent = pct_yolos / num_yolos
    elif asset_type == 'btc':
        percent = pct_btc
    elif asset_type == 'gold':
        percent = pct_gold
    else:
        percent = 0  # Default case if type is unknown

    assets[ticker] = {
        'percent': percent,
        'shares_owned': shares_owned
    }


# Scrape prices and yields from Yahoo! Finance and add these data to assets obj.
def update_asset_data():
    global total_portfolio_value, total_cash
    btc_wallet_value = 0
    tfsa_value = 0

    for ticker in assets:
        print(f"Processing {ticker}")
        # Scaping here.
        data = get_data_by_ticker(ticker)
        if data:
            # Updating assets object with price and dividend yield.
            assets[ticker]['price'] = data['price']
            assets[ticker]['yield'] = data['yield']

            # Update portfolio value.
            asset_value = assets[ticker]['price'] * assets[ticker]['shares_owned']
            if ticker == "BTC-USD":
                btc_wallet_value += asset_value
            else:
                tfsa_value += asset_value
            # Can add something here later for physical gold, bonds, etc.

        # Wait for 1 second before the next request so I don't get banned for scraping.
        time.sleep(1)

    # Calculate total cash owned converted to USD.
    total_cash += usd_owned
    forex_data = get_data_by_ticker('CADUSD%3DX')
    if forex_data:
        conversion_rate = forex_data['price']
        cad_owned_in_usd = cad_owned * conversion_rate
        total_cash += cad_owned_in_usd

    # Update total portfolio value
    total_portfolio_value += (btc_wallet_value + tfsa_value + total_cash)

    print()


# Print portfolio.
def print_portfolio():
    print("TARGET COMPOSITION")
    print(f"VT = {pct_vt * 100:.0f}%")
    print(f"VOO = {pct_voo * 100:.0f}%")
    print(f"ETF_DIVS = {pct_etf_divs * 100:.0f}%")
    print(f"IDV_DIVS = {pct_idv_divs * 100:.0f}%")
    print(f"GOLD = {pct_gold * 100:.0f}%")
    print(f"BTC = {pct_btc * 100:.0f}%")
    #print(f"YOLOS = {pct_yolos * 100:.0f}%")
    print()

    print("PORTFOLIO")
    total_yr_dividends = 0
    net_worth = 0
    for ticker, data in assets.items():
        shares_owned = data['shares_owned']
        total_stock_value = data['price'] * data['shares_owned']
        net_worth += total_stock_value
        target = data['percent'] * 100
        actual = (total_stock_value / total_portfolio_value) * 100
        yr_dividends = total_stock_value * data['yield']
        total_yr_dividends += yr_dividends
        
        # Define fixed-width columns when printing (adjust the widths as needed)
        ticker_fmt = "{:<8}"
        shares_fmt = "{:<15}"
        value_fmt = "{:<15}"
        target_fmt = "{:<15}"
        actual_fmt = "{:<15}"
        dividend_fmt = "{:15}"
        
        if ticker == "BTC-USD":
            print(f"{ticker_fmt.format('Bitcoin')} | {shares_fmt.format(f'{shares_owned} btc')} | {value_fmt.format(f'${total_stock_value:.2f} total')} | {target_fmt.format(f'{target:.2f}% target')} | {actual_fmt.format(f'{actual:.2f}% actual')}")
        elif ticker == "GC=F":
            print(f"{ticker_fmt.format('Gold')} | {shares_fmt.format(f'{shares_owned} oz')} | {value_fmt.format(f'${total_stock_value:.2f} total')} | {target_fmt.format(f'{target:.2f}% target')} | {actual_fmt.format(f'{actual:.2f}% actual')}")
        else:
            print(f"{ticker_fmt.format(ticker)} | {shares_fmt.format(f'{shares_owned} shares')} | {value_fmt.format(f'${total_stock_value:.2f} total')} | {target_fmt.format(f'{target:.2f}% target')} | {actual_fmt.format(f'{actual:.2f}% actual')} | {dividend_fmt.format(f'${yr_dividends:.2f} divs/yr')}")
    print()

    print("USD")
    print(f"${total_cash:.2f}")
    print()

    print("ANNUAL DIVIDEND INCOME")
    print(f"${total_yr_dividends:.2f}")
    print()

    print("NET WORTH")
    print(f"${net_worth:.2f}")
    print()


# Determine how much of what must be bought or sold to reach target percent allocations.
def rebalance_portfolio():
    print("REBALANCE")
    for ticker, data in assets.items():
        current_value = data['shares_owned'] * data['price']
        target_value = total_portfolio_value * data['percent']
        difference_value = target_value - current_value
        shares_needed = difference_value / data['price']

        # Set the threshold for deciding the action
        if ticker == "BTC-USD" or ticker == "GC=F":  # Allow fractional buys for Bitcoin and Gold
            if shares_needed > 0:
                action = "Buy"
            elif shares_needed < 0:
                action = "Sell"
            else:
                action = "Hold"
        else:
            # For stocks, ensure we're dealing with whole shares
            if shares_needed >= 1:
                action = "Buy"
            elif shares_needed <= -1:
                action = "Sell"
            else:
                action = "Hold"

        if action != "Hold":
            if ticker == "BTC-USD":
                print(f"{action} {abs(shares_needed):.8f} Bitcoin to reach the target allocation.")
            elif ticker == "GC=F":
                print(f"{action} {abs(shares_needed):.2f} ounces of gold to reach the target allocation.")
            else:
                print(f"{action} {abs(shares_needed):.2f} shares of {ticker} to reach the target allocation.")

        '''
        elif action == "Hold":
            if ticker == "BTC-USD":
                print("Hold Bitcoin")
            elif ticker == "GC=F":
                print("Hold Gold")
            else:
                print(f"Hold {ticker}")
        '''
    print()

update_asset_data()  # Update asset data before rebalancing
print_portfolio()
rebalance_portfolio()



