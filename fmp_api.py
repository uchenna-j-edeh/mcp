import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get('FMP_API_KEY', 'YOUR_API_KEY')
BASE_URL = "https://financialmodelingprep.com/api/v3"

def get_gainers(is_historical=False, specific_date=None):
    """Fetches gainers from the FMP API."""
    if is_historical:
        url = f"{BASE_URL}/historical-price-full/gainers?date={specific_date}&apikey={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get('historical', [])
    else:
        url = f"{BASE_URL}/stock_market/gainers?apikey={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

def get_losers(is_historical=False, specific_date=None):
    """Fetches losers from the FMP API."""
    if is_historical:
        url = f"{BASE_URL}/historical-price-full/losers?date={specific_date}&apikey={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get('historical', [])
    else:
        url = f"{BASE_URL}/stock_market/losers?apikey={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
