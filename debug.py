import os
from dotenv import load_dotenv

# Print current working directory
print("Current working directory:", os.getcwd())

# Check if .env file exists
print(".env file exists:", os.path.exists('.env'))

# Try to load and print environment variable (safely)
load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')
if api_key:
    print("API key found! First 10 characters:", api_key[:10])
else:
    print("API key not found!") 