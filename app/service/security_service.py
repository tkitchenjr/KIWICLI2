from app.service.alpha_vantage_client import get_company_name


class SecurityException(Exception):
    pass

def get_security_by_ticker(ticker: str):
    try:
        return get_company_name(ticker)
    except Exception as e:
        raise SecurityException(f'Failed to retrieve security due to error: {str(e)}')
