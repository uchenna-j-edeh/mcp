
import os
from flask import Flask, render_template
import requests
from datetime import datetime

app = Flask(__name__)

def get_color(percentage, max_percentage, is_gainer):
    """
    Calculates the color shade based on the percentage change relative to the max change.
    """
    # Normalize the percentage from 0 to 1
    if max_percentage == 0:
        normalized_percentage = 0
    else:
        normalized_percentage = abs(percentage) / max_percentage

    # Create a gradient from light to dark
    if is_gainer:
        # Green shades for gainers
        alpha = 0.1 + (normalized_percentage * 0.9)
        return f"rgba(0, 255, 0, {alpha})"
    else:
        # Red shades for losers
        alpha = 0.1 + (normalized_percentage * 0.9)
        return f"rgba(255, 0, 0, {alpha})"

@app.route('/')
def index():
    """
    Fetches top 10 gaining and losing stocks from the Financial Modeling Prep API
    and renders them in the index.html template.
    """
    api_key = os.environ.get('FMP_API_KEY', 'YOUR_API_KEY')  # Use environment variable or placeholder
    gainers_url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={api_key}"
    losers_url = f"https://financialmodelingprep.com/api/v3/stock_market/losers?apikey={api_key}"
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Fetch gainers
        gainers_response = requests.get(gainers_url)
        gainers_response.raise_for_status()
        gainers_data = gainers_response.json()
        top_10_gainers = gainers_data[:10]

        if top_10_gainers:
            max_gain = max(stock['changesPercentage'] for stock in top_10_gainers)
            for stock in top_10_gainers:
                stock['color'] = get_color(stock['changesPercentage'], max_gain, is_gainer=True)

        # Fetch losers
        losers_response = requests.get(losers_url)
        losers_response.raise_for_status()
        losers_data = losers_response.json()
        top_10_losers = losers_data[:10]

        if top_10_losers:
            max_loss = max(abs(stock['changesPercentage']) for stock in top_10_losers)
            for stock in top_10_losers:
                stock['color'] = get_color(stock['changesPercentage'], max_loss, is_gainer=False)

        return render_template('index.html', gainers=top_10_gainers, losers=top_10_losers, last_updated=now)

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
