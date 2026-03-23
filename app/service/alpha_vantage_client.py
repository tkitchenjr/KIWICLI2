from app.config import Config
from dataclasses import dataclass
import requests
from flask_caching import SimpleCache

# Initialize Cache variable
cache = SimpleCache(default_timeout=300) 


#Alpha Vantage Error Handling
class AlphaVantageError(Exception):
    pass

#Security Quote Dataclass
# ticker - str
# date - str
# price - float
# issuer - str

@dataclass
class SecurityQuote:
    ticker: str
    date: str
    price: float
    issuer: str

# get_api_key() -> str
#Private helper function to retrieve the API key from the application configuration
def get_api_key():
    api_key = Config.ALPHAVANTAGE_API_KEY
    if not api_key:
        raise AlphaVantageError('Alpha Vantage API key is not configured. Please set the API_KEY environment variable.')
    return api_key

# get_company_name(ticker:str) ->str |None — 
# Queries the Alpha Vantage API and returns the issuer name associated with the given ticker symbol. 
# Returns None if the ticker is not found.
def get_company_name(ticker: str):

    # Check Cache 
    key = f'company_name_{ticker}'
    cached_name = cache.get(key)
    if cached_name is not None:
        return cached_name
    
    # Defer to API if not in cache
    api_key = get_api_key()
    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}'

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    if not data:
        raise AlphaVantageError('No matching ticker found.')
    if not "Name" in data:
        return None
    
    # Cache the result before returning
    cache.set(key, data.get("Name"))
    return data.get("Name")

# get_price_data(ticker: str) -> dict | None — 
# Retrieves the most recent available price data for a given ticker. 
# Returns a dictionary with price fields (e.g., open, high, low, close, volume). 
# Returns None if data is unavailable.
def get_price_data(ticker: str) -> dict | None:
    # Check Cache
    key = f'price_data_{ticker.upper()}'
    cached_data = cache.get(key)
    if cached_data is not None:
        return cached_data

    api_key = get_api_key()
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval=5min&apikey={api_key}'

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    if "Time Series (5min)" not in data:
        return None

    time_series = data["Time Series (5min)"]
    latest_timestamp = max(time_series.keys())
    data = time_series[latest_timestamp]

    result = {
        'date': latest_timestamp,
        'close': float(data["4. close"]),
        
    }
    # Cache the result before returning
    cache.set(key, result)
    return result

# get_quote(ticker: str) -> SecurityQuote | None 
# A convenience function that calls get_company_name and get_price_data internally
# Returns a SecurityQuote dataclass instance or None if the ticker cannot be resolved.
def get_quote(ticker: str):
    company_name = get_company_name(ticker)
    if company_name is None:
        return None
    price_data = get_price_data(ticker)
    if price_data is None:
        return None
    return SecurityQuote(
        ticker=ticker.upper(),
        date=price_data['date'],
        price=price_data['close'],
        issuer=company_name
    )

