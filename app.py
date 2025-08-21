import os
import json
from flask import Flask, render_template
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

CACHE_DIR = '.data'
CACHE_EXPIRATION = timedelta(days=1)

def get_color(percentage, max_percentage, is_gainer):
    """
    Calculates the color shade based on the percentage change relative to the max change.
    """
    if max_percentage == 0:
        normalized_percentage = 0
    else:
        normalized_percentage = abs(percentage) / max_percentage

    if is_gainer:
        alpha = 0.1 + (normalized_percentage * 0.9)
        return f"rgba(0, 255, 0, {alpha})"
    else:
        alpha = 0.1 + (normalized_percentage * 0.9)
        return f"rgba(255, 0, 0, {alpha})"

def get_cached_data(filename):
    """
    Gets data from a cache file if it exists and is not expired.
    """
    filepath = os.path.join(CACHE_DIR, filename)
    if os.path.exists(filepath):
        modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        if datetime.now() - modified_time < CACHE_EXPIRATION:
            with open(filepath, 'r') as f:
                return json.load(f)
    return None

def set_cached_data(filename, data):
    """
    Saves data to a cache file.
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    filepath = os.path.join(CACHE_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f)

def get_sector(symbol, api_key):
    """
    Gets the sector for a stock, using a cache to avoid repeated API calls.
    """
    sectors = get_cached_data('sectors.json') or {}
    if symbol in sectors:
        return sectors[symbol]

    profile_url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={api_key}"
    try:
        profile_response = requests.get(profile_url)
        profile_response.raise_for_status()
        profile_data = profile_response.json()
        sector = profile_data[0].get('sector', 'N/A') if profile_data else 'N/A'
        sectors[symbol] = sector
        set_cached_data('sectors.json', sectors)
        return sector
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sector for {symbol}: {e}")
        return "N/A"

@app.route('/')
def index():
    """
    Fetches top 25 gaining and losing stocks from the Financial Modeling Prep API
    and renders them in the index.html template.
    """
    api_key = os.environ.get('FMP_API_KEY', 'YOUR_API_KEY')
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Fetch gainers
        gainers_data = get_cached_data('gainers.json')
        if not gainers_data:
            gainers_url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={api_key}"
            gainers_response = requests.get(gainers_url)
            gainers_response.raise_for_status()
            gainers_data = gainers_response.json()
            set_cached_data('gainers.json', gainers_data)

        top_25_gainers = gainers_data[:25]

        if top_25_gainers:
            max_gain = max(stock['changesPercentage'] for stock in top_25_gainers)
            for stock in top_25_gainers:
                stock['color'] = get_color(stock['changesPercentage'], max_gain, is_gainer=True)
                stock['sector'] = get_sector(stock['symbol'], api_key)


        # Fetch losers
        losers_data = get_cached_data('losers.json')
        if not losers_data:
            losers_url = f"https://financialmodelingprep.com/api/v3/stock_market/losers?apikey={api_key}"
            losers_response = requests.get(losers_url)
            losers_response.raise_for_status()
            losers_data = losers_response.json()
            set_cached_data('losers.json', losers_data)

        top_25_losers = losers_data[:25]

        if top_25_losers:
            max_loss = max(abs(stock['changesPercentage']) for stock in top_25_losers)
            for stock in top_25_losers:
                stock['color'] = get_color(stock['changesPercentage'], max_loss, is_gainer=False)
                stock['sector'] = get_sector(stock['symbol'], api_key)

        return render_template('index.html', gainers=top_25_gainers, losers=top_25_losers, last_updated=now)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from FMP API: {e}")
        return "Error fetching data. Please check your API key and network connection.", 500
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error processing data: {e}")
        return "Error processing data from the API.", 500

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Flask Stock App')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='The hostname to listen on.')
    parser.add_argument('--port', type=int, default=5000,
                        help='The port of the webserver.')
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=True)
