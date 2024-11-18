import os
from dotenv import load_dotenv

# Print current working directory
print("Current working directory:", os.getcwd())

# Check if .env file exists
print(".env file exists:", os.path.exists('.env'))

# Try to load and print environment variables (safely)
load_dotenv()

# Check Mulesoft credentials
mulesoft_url = os.getenv('MULESOFT_API_URL')
oauth_client_id = os.getenv('OAUTH_CLIENT_ID')
oauth_client_secret = os.getenv('OAUTH_CLIENT_SECRET')
oauth_token_url = os.getenv('OAUTH_TOKEN_URL')

if all([mulesoft_url, oauth_client_id, oauth_client_secret, oauth_token_url]):
    print("✅ Mulesoft configuration found!")
    print("API URL:", mulesoft_url)
    print("OAuth Token URL:", oauth_token_url)
    print("Client ID found (first 8 chars):", oauth_client_id[:8])
else:
    print("❌ Missing Mulesoft configuration!")
    print("Missing variables:", [
        var for var, value in {
            'MULESOFT_API_URL': mulesoft_url,
            'OAUTH_CLIENT_ID': oauth_client_id,
            'OAUTH_CLIENT_SECRET': oauth_client_secret,
            'OAUTH_TOKEN_URL': oauth_token_url
        }.items() if not value
    ]) 