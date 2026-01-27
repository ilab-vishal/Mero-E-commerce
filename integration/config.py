import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv():
        return False

load_dotenv()

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8050"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
APP_NAME = "EcommerceIntegration"

print(f"DEBUG: Config loaded - Host: {APP_HOST}, Port: {APP_PORT}")

# Elasticsearch Configuration
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTIC_USER = os.getenv("ELASTIC_USER", "elastic")
ELASTIC_PASS = os.getenv("ELASTIC_PASS", "password")

# Ngrok Configuration
NGROK_URL = os.getenv("NGROK_URL", "")