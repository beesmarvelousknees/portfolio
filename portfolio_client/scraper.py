import requests
from bs4 import BeautifulSoup

def get_data_by_ticker(ticker):
    # Construct the URL for the stock information page
    url = f"https://finance.yahoo.com/quote/{ticker}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    try:
        # Send a request to the website
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the stock price
        price_tag = soup.find('span', {'data-testid': 'qsp-price'})
        price = float(price_tag.text.replace(',', '')) if price_tag else None

        # List of possible titles to find the yield data
        yield_titles = ["Forward Dividend & Yield", "Yield"]

        dividend_yield_title = None
        for title in yield_titles:
            dividend_yield_title = soup.find('span', string=title)
            if dividend_yield_title:
                break

        if dividend_yield_title:
            # Find the next sibling span containing the yield data
            yield_tag = dividend_yield_title.find_next_sibling('span')
            if yield_tag:
                yield_text = yield_tag.text
                # Extract the yield percentage by parsing backward from the percent sign
                percent_index = yield_text.find('%')
                if percent_index != -1:
                    start_index = percent_index - 1
                    while start_index >= 0 and (yield_text[start_index].isdigit() or yield_text[start_index] in '.'):
                        start_index -= 1
                    yield_percentage_part = yield_text[start_index + 1:percent_index]
                    yield_value = float(yield_percentage_part) / 100
                else:
                    yield_value = 0
            else:
                yield_value = 0
        else:
            yield_value = 0

        return {'price': price, 'yield': yield_value}

    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

'''
# Example usage
tickers = ['CADUSD%3DX']
for ticker in tickers:
    result = get_data_by_ticker(ticker)
    print(f"Processing {ticker}: {result}")
'''
