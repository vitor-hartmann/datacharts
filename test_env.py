import os
from dotenv import load_dotenv

# Get absolute path to .env file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')

print(f"Looking for .env file at: {ENV_PATH}")
print(f".env file exists: {os.path.exists(ENV_PATH)}")

# Load the .env file
load_dotenv(ENV_PATH)

# Check Mulesoft configuration
required_vars = {
    'MULESOFT_API_URL': os.getenv('MULESOFT_API_URL'),
    'OAUTH_CLIENT_ID': os.getenv('OAUTH_CLIENT_ID'),
    'OAUTH_CLIENT_SECRET': os.getenv('OAUTH_CLIENT_SECRET'),
    'OAUTH_TOKEN_URL': os.getenv('OAUTH_TOKEN_URL')
}

missing_vars = [var for var, value in required_vars.items() if not value]

if not missing_vars:
    print("✅ All Mulesoft configuration variables found!")
    print(f"API URL: {required_vars['MULESOFT_API_URL']}")
    print(f"OAuth Token URL: {required_vars['OAUTH_TOKEN_URL']}")
    print(f"Client ID (first 8 chars): {required_vars['OAUTH_CLIENT_ID'][:8]}")
else:
    print("❌ Missing required variables:", missing_vars) 