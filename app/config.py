import os
from dotenv import load_dotenv

#Global Alpha Vantage Error Handling
class AlphaVantageError(Exception):
    pass
load_dotenv()
load_dotenv('api_key.env')


class Config:
    ALPHAVANTAGE_API_KEY = os.environ.get('API_KEY')

# get_api_key() -> str
#Private helper function to retrieve the API key from the application configuration
def get_api_key():
    api_key = Config.ALPHAVANTAGE_API_KEY
    if not api_key:
        raise AlphaVantageError('Alpha Vantage API key is not configured. Please set the API_KEY environment variable.')
    return api_key

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite:///:memory:'
    SQLALCHEMY_ECHO = False


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://kiwi_local:kiwilocaldb@localhost:3306/kiwilocal'
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        f'mysql+pymysql://{os.environ.get("DB_USER", "")}:'
        f'{os.environ.get("DB_PASSWORD", "")}@'
        f'{os.environ.get("DB_HOST", "")}:'
        f'{os.environ.get("DB_PORT", "3306")}/'
        f'{os.environ.get("DB_NAME", "")}'
    )
    DEBUG = False
    SQLALCHEMY_ECHO = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestConfig,
}


def get_config(env: str):
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)
