from dataclasses import dataclass
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv('api_key.env')


class AlphaVantageError(Exception):
    pass


@dataclass
class SecurityQuote:
    ticker: str
    date: str
    price: float
    issuer: str


_CACHE_PATH = Path(__file__).resolve().parents[2] / 'instance' / 'quote_cache.json'


def _load_cache() -> dict:
    if not _CACHE_PATH.exists():
        return {}

    try:
        with _CACHE_PATH.open('r', encoding='utf-8') as cache_file:
            payload = json.load(cache_file)
            return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _save_cache(cache_data: dict):
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _CACHE_PATH.open('w', encoding='utf-8') as cache_file:
        json.dump(cache_data, cache_file)


def _cache_price_data(ticker: str, price_data: dict):
    normalized_ticker = ticker.upper()
    cache_data = _load_cache()
    cache_data[normalized_ticker] = {
        'date': price_data.get('date', ''),
        'open': float(price_data.get('open', price_data['close'])),
        'high': float(price_data.get('high', price_data['close'])),
        'low': float(price_data.get('low', price_data['close'])),
        'close': float(price_data['close']),
        'volume': int(price_data.get('volume', 0)),
    }
    _save_cache(cache_data)


def _get_cached_price_data(ticker: str):
    normalized_ticker = ticker.upper()
    cached = _load_cache().get(normalized_ticker)
    if not cached:
        # Fallback to latest real trade price already stored in our DB.
        # This is still a real historical market-derived value, not a placeholder.
        cached_from_db = _get_cached_price_data_from_transactions(normalized_ticker)
        if not cached_from_db:
            return None
        _cache_price_data(normalized_ticker, cached_from_db)
        return cached_from_db

    return {
        'date': cached.get('date', ''),
        'open': float(cached['open']),
        'high': float(cached['high']),
        'low': float(cached['low']),
        'close': float(cached['close']),
        'volume': int(cached.get('volume', 0)),
    }


def _get_cached_price_data_from_transactions(ticker: str):
    try:
        from app.db import db
        from app.models import Transaction

        latest_trade = (
            db.session.query(Transaction)
            .filter(Transaction.ticker == ticker)
            .order_by(Transaction.date_time.desc())
            .first()
        )
        if not latest_trade:
            return None

        price = float(latest_trade.price)
        return {
            'date': latest_trade.date_time.isoformat() if latest_trade.date_time else '',
            'open': price,
            'high': price,
            'low': price,
            'close': price,
            'volume': 0,
        }
    except Exception:
        return None


def _rate_limited(payload: dict) -> bool:
    return bool(payload.get('Note') or payload.get('Information'))


def get_api_key():
    api_key = (
        os.environ.get('API_KEY')
        or os.environ.get('ALPHAVANTAGE_API_KEY')
        or os.environ.get('ALPHA_VANTAGE_API_KEY')
        or os.environ.get('VITE_ALPHA_VANTAGE_API_KEY')
    )
    if not api_key:
        raise AlphaVantageError(
            'Alpha Vantage API key is not configured. Set one of: '
            'API_KEY, ALPHAVANTAGE_API_KEY, or ALPHA_VANTAGE_API_KEY '
            '(for local development, add API_KEY=<your_key> to api_key.env).'
        )
    return api_key


def get_company_name(ticker: str):
    api_key = get_api_key()
    normalized_ticker = ticker.upper()
    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={normalized_ticker}&apikey={api_key}'

    response = requests.get(url, timeout=20)
    response.raise_for_status()
    payload = response.json()

    if _rate_limited(payload):
        return normalized_ticker

    if not payload:
        raise AlphaVantageError('No matching ticker found.')

    return payload.get('Name') or normalized_ticker


def _get_global_quote(api_key: str, ticker: str):
    normalized_ticker = ticker.upper()
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={normalized_ticker}&apikey={api_key}'

    response = requests.get(url, timeout=20)
    response.raise_for_status()
    payload = response.json()

    if _rate_limited(payload):
        cached = _get_cached_price_data(normalized_ticker)
        if cached:
            return cached
        raise AlphaVantageError(
            'Alpha Vantage request limit reached and no cached quote is available yet for this symbol.'
        )

    quote_data = payload.get('Global Quote', {})
    if not quote_data or not quote_data.get('05. price'):
        return None

    parsed = {
        'date': quote_data.get('07. latest trading day') or '',
        'open': float(quote_data.get('02. open', quote_data['05. price'])),
        'high': float(quote_data.get('03. high', quote_data['05. price'])),
        'low': float(quote_data.get('04. low', quote_data['05. price'])),
        'close': float(quote_data['05. price']),
        'volume': int(float(quote_data.get('06. volume', 0))),
    }
    _cache_price_data(normalized_ticker, parsed)
    return parsed


def get_price_data(ticker: str):
    api_key = get_api_key()
    normalized_ticker = ticker.upper()

    # Use GLOBAL_QUOTE first: this is free-tier compatible and lower-latency.
    global_quote = _get_global_quote(api_key, normalized_ticker)
    if global_quote is not None:
        return global_quote

    # Fallback to daily close when global quote is unavailable.
    daily_url = (
        'https://www.alphavantage.co/query?'
        f'function=TIME_SERIES_DAILY&symbol={normalized_ticker}&outputsize=compact&apikey={api_key}'
    )
    response = requests.get(daily_url, timeout=20)
    response.raise_for_status()
    payload = response.json()

    if _rate_limited(payload):
        cached = _get_cached_price_data(normalized_ticker)
        if cached:
            return cached
        raise AlphaVantageError(
            'Alpha Vantage request limit reached and no cached quote is available yet for this symbol.'
        )

    time_series = payload.get('Time Series (Daily)')
    if not time_series:
        return None

    latest_date = max(time_series.keys())
    latest = time_series[latest_date]

    parsed = {
        'date': latest_date,
        'open': float(latest['1. open']),
        'high': float(latest['2. high']),
        'low': float(latest['3. low']),
        'close': float(latest['4. close']),
        'volume': int(latest['5. volume']),
    }
    _cache_price_data(normalized_ticker, parsed)
    return parsed


def get_quote(ticker: str):
    normalized_ticker = ticker.upper()
    company_name = get_company_name(normalized_ticker)
    price_data = get_price_data(normalized_ticker)
    if price_data is None:
        return None

    return SecurityQuote(
        ticker=normalized_ticker,
        date=price_data['date'],
        price=price_data['close'],
        issuer=company_name,
    )
