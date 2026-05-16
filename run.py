import os

from app import create_app
from app.config import DevelopmentConfig

app = create_app(DevelopmentConfig)

if __name__ == "__main__":
    app.run(port=int(os.environ.get('PORT', '5050')))
